"""Resumable, sequential Speech/LLM acceptance campaign with durable reports."""

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

from backend.services.ai_contracts import AISettings, EvaluationResult, ServiceError, SpeechResult
from backend.services.llm_service import evaluate_interview_answer_llm
from backend.services.speech_service import analyze_filler_words, transcribe_audio_whisper

ROOT = Path(__file__).resolve().parents[1]
LOCAL_TZ = timezone(timedelta(hours=7))
SOURCE_FILES = (
    'backend/services/ai_contracts.py', 'backend/services/speech_service.py',
    'backend/services/llm_service.py', 'scripts/run_speech_llm_campaign.py',
)


class CampaignError(RuntimeError):
    """Messages safe to display without environment/provider error bodies."""


def now():
    return datetime.now(LOCAL_TZ)


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_settings(mode):
    load_dotenv(ROOT / '.env', override=False)
    return AISettings.from_env().model_copy(update={'mode': mode, 'allow_fallback': False})


def public_settings(settings):
    return settings.model_dump(mode='json', exclude={'groq_api_key', 'gemini_api_key'})


def create_plan(directory, settings, start, counts=(9, 9, 12), interval=30, gap=7200, target=3):
    if len(counts) != 3 or any(n <= 0 or n % 3 for n in counts):
        raise CampaignError('Mỗi đợt phải có số lượt dương, chia hết cho 3; cần đúng 3 đợt.')
    if not all(math.isfinite(v) for v in (interval, gap, target)) or interval < 0 or gap < 0 or target <= 0:
        raise CampaignError('Khoảng nghỉ không âm; ngưỡng thời gian phải dương.')
    cases = []
    for n in range(1, 4):
        media = f'tests/fixtures/answer_vi_{n:02d}.webm'
        reference = f'tests/fixtures/answer_vi_{n:02d}.txt'
        cases.append({'id': f'answer_vi_{n:02d}', 'media': media, 'reference': reference,
                      'media_sha256': digest(ROOT / media), 'reference_sha256': digest(ROOT / reference),
                      'expected_fillers': analyze_filler_words((ROOT / reference).read_text(encoding='utf-8-sig'))})
    plan = {'version': 1, 'created_at': now().isoformat(), 'start_at': start.isoformat(),
            'timezone': 'UTC+07:00', 'interval_seconds': interval,
            'gap_after_batch_seconds': gap, 'target_seconds': target,
            'settings': public_settings(settings),
            'source_sha256': {name: digest(ROOT / name) for name in SOURCE_FILES},
            'question': 'Tell me about a difficult project problem you solved.',
            'role': 'Software Engineer', 'language': 'vi', 'cases': cases,
            'client_policy': 'new clients per trial, identical to previous CLI benchmarks',
            'scope': 'WebM decode + Groq STT/timestamps/fillers + Gemini + schema validation; excludes recording/upload/FER/DB/frontend, report writing and waits',
            'batches': [], 'trials': []}
    number = 1
    for batch, count in enumerate(counts, 1):
        ids = list(range(number, number + count))
        plan['batches'].append({'batch': batch, 'trial_ids': ids})
        for index, trial_id in enumerate(ids):
            plan['trials'].append({'id': trial_id, 'batch': batch, 'case': cases[index % 3]['id']})
        number += count
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'trials').mkdir()
    atomic_json(directory / 'plan.json', plan)
    write_summary(directory, plan, [])
    return plan


def records_for(directory, plan):
    records = []
    for trial in plan['trials']:
        path = directory / 'trials' / f"trial-{trial['id']:03d}.json"
        if path.exists():
            record = read_json(path)
            if (record['id'], record['batch'], record['case']) != (trial['id'], trial['batch'], trial['case']):
                raise CampaignError('Báo cáo lượt không khớp kế hoạch; không ghi đè.')
            records.append(record)
    return records


def stats(records, planned):
    finished = [r for r in records if r['status'] != 'running']
    live = [r for r in finished if r.get('benchmark', {}).get('measured_live')]
    passed = [r for r in live if r['benchmark']['target_met'] is True]
    values = sorted(r['benchmark']['total_seconds'] for r in live)
    errors = {}
    for r in finished:
        code = r.get('error', {}).get('code')
        if code:
            errors[code] = errors.get(code, 0) + 1
    return {'planned': planned, 'finished': len(finished), 'running': len(records) - len(finished),
            'remaining': planned - len(finished), 'live_completed': len(live),
            'latency_passed': len(passed), 'errors': errors,
            'pass_rate_of_finished': len(passed) / len(finished) if finished else None,
            'live_success_rate': len(live) / len(finished) if finished else None,
            'median_seconds': statistics.median(values) if values else None,
            'p95_seconds': values[math.ceil(0.95 * len(values)) - 1] if values else None,
            'max_seconds': max(values) if values else None,
            'strict_latency_accepted': len(finished) == planned and len(passed) == planned}


def batch_due(plan, batch, records):
    if batch == 1:
        return datetime.fromisoformat(plan['start_at'])
    previous_ids = plan['batches'][batch - 2]['trial_ids']
    previous = [r for r in records if r['id'] in previous_ids and r['status'] != 'running']
    if len(previous) != len(previous_ids):
        return None
    return max(datetime.fromisoformat(r['finished_at']) for r in previous) + timedelta(seconds=plan['gap_after_batch_seconds'])


def write_summary(directory, plan, records):
    summary = {'updated_at': now().isoformat(), 'mode': plan['settings']['mode'],
               'gemini_model': plan['settings']['gemini_model'], 'target_seconds': plan['target_seconds'],
               'statistics_scope': 'latency statistics use completed real API trials only; failed/interrupted/mock trials remain in counts and pass-rate denominator',
               'quality_review': 'manual review required; latency pass does not establish transcript/feedback accuracy',
               'overall': stats(records, len(plan['trials'])),
               'batches': [], 'cases': []}
    for batch in plan['batches']:
        due = batch_due(plan, batch['batch'], records)
        summary['batches'].append({'batch': batch['batch'], 'due_at': due.isoformat() if due else None,
                                   **stats([r for r in records if r['batch'] == batch['batch']], len(batch['trial_ids']))})
    for case in plan['cases']:
        summary['cases'].append({'case': case['id'], **stats([r for r in records if r['case'] == case['id']],
                                                            sum(t['case'] == case['id'] for t in plan['trials']))})
    atomic_json(directory / 'summary.json', summary)
    fields = ['id', 'batch', 'case', 'status', 'started_at', 'finished_at', 'speech_seconds',
              'llm_seconds', 'total_seconds', 'measured_live', 'target_met', 'content_score',
              'filler_words_count', 'expected_filler_words_count', 'error_code', 'report']
    temporary = directory / 'results.csv.tmp'
    with temporary.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = {k: r.get(k) for k in ('id', 'batch', 'case', 'status', 'started_at', 'finished_at')}
            speech = r.get('speech', {}); llm = r.get('llm', {})
            row.update(speech_seconds=speech.get('seconds'), llm_seconds=llm.get('seconds'),
                       content_score=llm.get('result', {}).get('content_score'),
                       filler_words_count=speech.get('result', {}).get('filler_words_count'),
                       expected_filler_words_count=r.get('expected_fillers', {}).get('filler_words_count'),
                       error_code=r.get('error', {}).get('code'), report=f"trials/trial-{r['id']:03d}.json")
            row.update({k: r.get('benchmark', {}).get(k) for k in ('total_seconds', 'measured_live', 'target_met')})
            writer.writerow(row)
    temporary.replace(directory / 'results.csv')
    overall = summary['overall']
    lines = ['# Báo cáo chiến dịch Speech → LLM', '',
             f"Model: `{summary['gemini_model']}`. Mode: `{summary['mode']}`. Ngưỡng: < {plan['target_seconds']} giây.", '',
             f"Đã kết thúc {overall['finished']}/{overall['planned']} lượt; API thật hoàn thành {overall['live_completed']}; đạt thời gian {overall['latency_passed']}.",
             f"Nghiệm thu toàn chiến dịch về độ trễ: **{'ĐẠT' if overall['strict_latency_accepted'] else 'CHƯA ĐẠT / CHƯA ĐỦ LƯỢT'}**.", '',
             'Thống kê thời gian chỉ dùng lượt API thật hoàn thành; lỗi/mock/gián đoạn vẫn được giữ và tính vào mẫu số tỷ lệ đạt.',
             'P95 dùng nearest-rank. Chất lượng transcript, căn từ timestamps và việc LLM bịa thông tin cần đối chiếu thủ công.',
             'Thời gian chờ giữa lượt/đợt và ghi báo cáo nằm ngoài phép đo. Phạm vi không gồm upload/FER/DB/frontend.', '',
             '| Đợt | Lượt | Đã xong | Đạt < ngưỡng | Bắt đầu sớm nhất (UTC+7) |',
             '|---|---:|---:|---:|---|']
    for b in summary['batches']:
        pending = f"{plan['gap_after_batch_seconds'] / 3600:g} giờ sau khi đợt trước kết thúc"
        lines.append(f"| {b['batch']} | {b['planned']} | {b['finished']} | {b['latency_passed']} | {b['due_at'] or pending} |")
    lines += ['', '| Lượt | Đợt | Audio | Trạng thái | Speech (s) | LLM (s) | Tổng (s) | Đạt | Lỗi |',
              '|---|---:|---|---|---:|---:|---:|---|---|']
    def number(value):
        return f'{value:.3f}' if value is not None else '—'
    for r in records:
        b = r.get('benchmark', {})
        lines.append(f"| [{r['id']:03d}](trials/trial-{r['id']:03d}.json) | {r['batch']} | {r['case']} | {r['status']} | "
                     f"{number(r.get('speech', {}).get('seconds'))} | {number(r.get('llm', {}).get('seconds'))} | "
                     f"{number(b.get('total_seconds'))} | {b.get('target_met')} | {r.get('error', {}).get('code', '')} |")
    lines += ['', '## Thống kê lượt hoàn thành bằng API thật', '',
              f"- Trung vị: {number(overall['median_seconds'])} s.",
              f"- P95: {number(overall['p95_seconds'])} s.",
              f"- Lớn nhất: {number(overall['max_seconds'])} s.", '',
              'Các lần lỗi không được thay bằng bản chép chuẩn hoặc tự thử lại để ghi nhận đạt. Lượt interrupted được giữ nguyên; khởi động lại tiếp tục lượt chưa bắt đầu.', '']
    (directory / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    return summary


@contextmanager
def campaign_lock(directory):
    with (directory / '.runner.lock').open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise CampaignError('Chiến dịch đang có tiến trình khác chạy; không chạy trùng.') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def call_service(operation, schema):
    started = time.perf_counter()
    try:
        result = schema.model_validate(operation()).model_dump(mode='json')
        report = {'status': 'ok', 'result': result}
    except ServiceError as exc:
        report = {'status': 'error', 'error': {'code': exc.code, 'message': str(exc)}}
    except Exception as exc:
        report = {'status': 'error', 'error': {'code': 'unexpected_service_error', 'exception_type': type(exc).__name__}}
    report['seconds'] = time.perf_counter() - started
    return report


def execute_trial(record, plan, settings, case):
    started = time.perf_counter()
    try:
        record['speech'] = call_service(lambda: transcribe_audio_whisper(ROOT / case['media'], language=plan['language'], settings=settings), SpeechResult)
        if record['speech']['status'] != 'ok':
            record['llm'] = {'status': 'skipped', 'reason': 'speech_failed'}
            record['error'] = {'stage': 'speech', **record['speech']['error']}
        else:
            speech = record['speech']['result']
            record['llm'] = call_service(lambda: evaluate_interview_answer_llm(
                question_text=plan['question'], role_name=plan['role'], transcript=speech['transcript'],
                filler_words_count=speech['filler_words_count'], speech_is_mock=speech['metadata']['is_mock'],
                settings=settings), EvaluationResult)
            if record['llm']['status'] != 'ok':
                record['error'] = {'stage': 'llm', **record['llm']['error']}
        elapsed = time.perf_counter() - started
        real = (settings.mode == 'live' and record['speech']['status'] == record['llm']['status'] == 'ok'
                and record['speech']['result']['metadata']['provider'] == 'groq'
                and record['llm']['result']['metadata']['provider'] == 'gemini'
                and not record['speech']['result']['metadata']['is_mock']
                and not record['llm']['result']['metadata']['is_mock'])
        record['benchmark'] = {'total_seconds': elapsed, 'target_seconds': plan['target_seconds'],
                               'measured_live': real, 'target_met': elapsed < plan['target_seconds'] if real else None}
        record['status'] = 'error' if 'error' in record else ('completed' if real else 'non_live')
        record['quality_review'] = 'pending'
    except KeyboardInterrupt:
        record.update(status='interrupted', error={'code': 'interrupted', 'message': 'Lượt bị dừng; không tự chạy lại.'})
        raise
    finally:
        record['finished_at'] = now().isoformat()


def validate_inputs(plan, settings):
    if public_settings(settings) != plan['settings']:
        raise CampaignError('Cấu hình đã đổi so với kế hoạch. Tạo chiến dịch mới để không trộn kết quả.')
    for name, expected in plan['source_sha256'].items():
        if digest(ROOT / name) != expected:
            raise CampaignError('Code đã đổi so với kế hoạch. Tạo chiến dịch mới.')
    for c in plan['cases']:
        if digest(ROOT / c['media']) != c['media_sha256'] or digest(ROOT / c['reference']) != c['reference_sha256']:
            raise CampaignError('Audio/bản chuẩn đã đổi so với kế hoạch. Tạo chiến dịch mới.')
    if settings.mode == 'live' and (not settings.groq_api_key or not settings.gemini_api_key):
        raise CampaignError('Thiếu GROQ_API_KEY hoặc GEMINI_API_KEY; chưa gửi API request.')


def run_campaign(directory, wait=False):
    with campaign_lock(directory):
        plan = read_json(directory / 'plan.json')
        settings = current_settings(plan['settings']['mode'])
        validate_inputs(plan, settings)
        records = records_for(directory, plan)
        for r in records:
            if r['status'] == 'running':
                r.update(status='interrupted', finished_at=now().isoformat(), error={'code': 'interrupted', 'message': 'Tiến trình trước đã dừng giữa lượt.'})
                atomic_json(directory / 'trials' / f"trial-{r['id']:03d}.json", r)
        write_summary(directory, plan, records)
        atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'running', 'updated_at': now().isoformat()})
        try:
            for trial in plan['trials']:
                if any(r['id'] == trial['id'] for r in records):
                    continue
                due = batch_due(plan, trial['batch'], records)
                if due is None:
                    raise CampaignError('Đợt trước chưa kết thúc; không thể chạy đợt tiếp theo.')
                if records:
                    due = max(due, max(datetime.fromisoformat(r['finished_at']) for r in records) + timedelta(seconds=plan['interval_seconds']))
                announced = False
                while now() < due:
                    atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'waiting',
                                'next_trial': trial['id'], 'next_batch': trial['batch'], 'due_at': due.isoformat(), 'updated_at': now().isoformat()})
                    if not wait:
                        print(f'PENDING trial={trial["id"]:03d} due={due.isoformat()}', flush=True)
                        return 4
                    if not announced:
                        print(f'WAIT batch={trial["batch"]} trial={trial["id"]:03d} due={due.isoformat()}', flush=True)
                        announced = True
                    time.sleep(min(30, max(0, (due - now()).total_seconds())))
                validate_inputs(plan, current_settings(plan['settings']['mode']))
                case = next(c for c in plan['cases'] if c['id'] == trial['case'])
                record = {**trial, 'status': 'running', 'started_at': now().isoformat(),
                          'media': case['media'], 'reference': case['reference'], 'expected_fillers': case['expected_fillers']}
                path = directory / 'trials' / f"trial-{trial['id']:03d}.json"
                atomic_json(path, record)
                atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'running', 'trial': trial['id'], 'batch': trial['batch'], 'updated_at': now().isoformat()})
                print(f'START batch={trial["batch"]} trial={trial["id"]:03d} case={trial["case"]}', flush=True)
                try:
                    execute_trial(record, plan, settings, case)
                finally:
                    atomic_json(path, record)
                    records.append(record)
                    write_summary(directory, plan, records)
                print(json.dumps({'trial': record['id'], 'status': record['status'],
                                  'benchmark': record.get('benchmark'), 'error': record.get('error')}, ensure_ascii=False), flush=True)
            summary = write_summary(directory, plan, records)
            atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'finished', 'updated_at': now().isoformat()})
            return 0 if summary['overall']['strict_latency_accepted'] else 1
        except KeyboardInterrupt:
            atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'stopped', 'updated_at': now().isoformat()})
            return 130
        except Exception:
            atomic_json(directory / 'runner.json', {'pid': os.getpid(), 'status': 'error', 'updated_at': now().isoformat()})
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    plan_parser = sub.add_parser('plan', help='Create frozen campaign; no API calls')
    plan_parser.add_argument('--output', type=Path, required=True)
    plan_parser.add_argument('--mode', choices=['live', 'mock'], default='live')
    plan_parser.add_argument('--start', default='now', help='now or ISO datetime; default timezone UTC+7')
    plan_parser.add_argument('--counts', default='9,9,12')
    plan_parser.add_argument('--interval-seconds', type=float, default=30)
    plan_parser.add_argument('--gap-hours', type=float, default=2)
    plan_parser.add_argument('--max-seconds', type=float, default=3)
    for action in ('run', 'report'):
        p = sub.add_parser(action)
        p.add_argument('--campaign', type=Path, required=True)
        if action == 'run':
            p.add_argument('--wait', action='store_true', help='Stay alive and automatically wait for later trials/batches')
    args = parser.parse_args(argv)
    try:
        if args.action == 'plan':
            start = now() if args.start == 'now' else datetime.fromisoformat(args.start)
            if start.tzinfo is None:
                start = start.replace(tzinfo=LOCAL_TZ)
            directory = args.output.resolve()
            create_plan(directory, current_settings(args.mode), start,
                        counts=tuple(int(n) for n in args.counts.split(',')),
                        interval=args.interval_seconds, gap=args.gap_hours * 3600, target=args.max_seconds)
            print(f'CREATED {directory}', flush=True)
            return 0
        directory = args.campaign.resolve()
        if args.action == 'run':
            return run_campaign(directory, args.wait)
        plan = read_json(directory / 'plan.json')
        print(json.dumps(write_summary(directory, plan, records_for(directory, plan))['overall'], ensure_ascii=False, indent=2))
        return 0
    except CampaignError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f'Không thể chạy chiến dịch ({type(exc).__name__}); kiểm tra đường dẫn/cấu hình.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
