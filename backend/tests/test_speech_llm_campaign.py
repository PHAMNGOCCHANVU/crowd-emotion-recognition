"""Campaign safety, scheduling and statistics, without live API calls/sleeps."""
from datetime import timedelta

import pytest

from backend.services.ai_contracts import AISettings, ServiceError
from scripts import run_speech_llm_campaign as campaign
from pathlib import Path
campaign.ROOT = Path(__file__).resolve().parents[2]
campaign.SOURCE_FILES = (
    'backend/services/ai_contracts.py', 'backend/services/speech_service.py',
    'backend/services/llm_service.py', 'backend/scripts/run_speech_llm_campaign.py',
)


def speech():
    return {'transcript': 'Answer', 'language': 'vi', 'words': [{'word': 'Answer', 'start': 0.0, 'end': 0.5}],
            'duration_seconds': 1.0, 'filler_words_count': 0, 'filler_words': {},
            'metadata': {'provider': 'groq', 'model': 'whisper-large-v3-turbo', 'is_mock': False, 'latency_ms': 100}}


def feedback():
    return {'content_score': 80, 'content_critique': 'Evidence', 'delivery_critique': 'No FER',
            'suggested_answer': 'Use actual evidence',
            'metadata': {'provider': 'gemini', 'model': 'gemini-3.8-flash', 'is_mock': False, 'latency_ms': 100}}


@pytest.fixture
def settings():
    return AISettings(groq_api_key='secret-groq-test', gemini_api_key='secret-gemini-test', allow_fallback=False)


def new_record():
    return {'id': 1, 'batch': 1, 'case': 'answer_vi_01', 'status': 'running', 'started_at': campaign.now().isoformat()}


def test_plan_30_trials_balanced_and_no_secrets(tmp_path, settings):
    directory = tmp_path / 'campaign'
    plan = campaign.create_plan(directory, settings, campaign.now())
    assert [len(b['trial_ids']) for b in plan['batches']] == [9, 9, 12]
    assert [sum(t['case'] == c['id'] for t in plan['trials']) for c in plan['cases']] == [10, 10, 10]
    assert plan['gap_after_batch_seconds'] == 7200 and plan['interval_seconds'] == 30
    contents = (directory / 'plan.json').read_text(encoding='utf-8')
    assert 'secret-groq-test' not in contents and 'secret-gemini-test' not in contents
    with pytest.raises(FileExistsError):
        campaign.create_plan(directory, settings, campaign.now())


def test_stt_failure_preserved_no_reference_substitution(monkeypatch, settings):
    def fail(*a, **kw):
        assert kw['settings'].allow_fallback is False
        raise ServiceError('speech_api_error', 'Groq HTTP 429')
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', fail)
    monkeypatch.setattr(campaign, 'evaluate_interview_answer_llm', lambda **kw: pytest.fail('LLM must not run'))
    record = new_record()
    campaign.execute_trial(record, {'language': 'vi', 'target_seconds': 3}, settings, {'media': 'unused.webm'})
    assert record['status'] == 'error' and record['error']['stage'] == 'speech'
    assert record['llm']['status'] == 'skipped'
    assert record['benchmark']['target_met'] is None


def test_llm_failure_retains_successful_speech(monkeypatch, settings):
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', lambda *a, **kw: speech())
    def fail(**kw):
        assert kw['transcript'] == 'Answer'
        raise ServiceError('llm_api_error', 'Gemini HTTP 504')
    monkeypatch.setattr(campaign, 'evaluate_interview_answer_llm', fail)
    record = new_record()
    campaign.execute_trial(record, {'language': 'vi', 'question': 'Question', 'role': 'Engineer', 'target_seconds': 3}, settings, {'media': 'unused'})
    assert record['speech']['result']['transcript'] == 'Answer'
    assert record['error']['stage'] == 'llm' and record['benchmark']['measured_live'] is False


def test_unexpected_exception_body_not_logged():
    def fail():
        raise RuntimeError('secret-credential-in-provider-body')
    result = campaign.call_service(fail, campaign.SpeechResult)
    assert 'secret-credential' not in str(result)
    assert result['error']['exception_type'] == 'RuntimeError'


@pytest.mark.parametrize('elapsed,passed', [(2.9999, True), (3.0, False), (3.0001, False)])
def test_latency_boundary_uses_full_unrounded_duration(monkeypatch, settings, elapsed, passed):
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', lambda *a, **kw: speech())
    monkeypatch.setattr(campaign, 'evaluate_interview_answer_llm', lambda **kw: feedback())
    # Overall start, STT start/end, LLM start/end, overall end.
    ticks = iter([0, 0, 1, 1, elapsed, elapsed])
    monkeypatch.setattr(campaign.time, 'perf_counter', lambda: next(ticks))
    record = new_record()
    campaign.execute_trial(record, {'language': 'vi', 'question': 'Q', 'role': 'E', 'target_seconds': 3}, settings, {'media': 'unused'})
    assert record['benchmark']['target_met'] is passed


def test_mock_never_passes_live_acceptance(monkeypatch):
    s = speech(); s['metadata'].update(provider='mock', is_mock=True)
    f = feedback(); f['metadata'].update(provider='mock', is_mock=True)
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', lambda *a, **kw: s)
    monkeypatch.setattr(campaign, 'evaluate_interview_answer_llm', lambda **kw: f)
    record = new_record()
    campaign.execute_trial(record, {'language': 'vi', 'question': 'Q', 'role': 'E', 'target_seconds': 3}, AISettings(mode='mock'), {'media': 'unused'})
    assert record['status'] == 'non_live' and record['benchmark']['target_met'] is None


def test_stats_count_failures_and_do_not_average_error_latency():
    records = [{'status': 'completed', 'benchmark': {'measured_live': True, 'target_met': t < 3, 'total_seconds': t}}
               for t in (1, 2, 4)]
    records.append({'status': 'error', 'error': {'code': '504'}, 'benchmark': {'measured_live': False, 'total_seconds': 60, 'target_met': None}})
    result = campaign.stats(records, 4)
    assert result['pass_rate_of_finished'] == 0.5
    assert result['median_seconds'] == 2 and result['p95_seconds'] == 4
    assert result['errors'] == {'504': 1} and not result['strict_latency_accepted']


def test_config_and_code_drift_rejected(tmp_path, settings):
    plan = campaign.create_plan(tmp_path / 'campaign', settings, campaign.now())
    with pytest.raises(campaign.CampaignError, match='Cấu hình'):
        campaign.validate_inputs(plan, settings.model_copy(update={'gemini_model': 'another-model'}))
    plan['source_sha256']['backend/services/llm_service.py'] = 'wrong-hash'
    with pytest.raises(campaign.CampaignError, match='Code'):
        campaign.validate_inputs(plan, settings)


def test_schedule_gap_from_batch_finish_resume_and_no_duplicates(tmp_path, settings, monkeypatch):
    class Clock:
        wall = campaign.now()
        seconds = 0
        sleeps = []
        def sleep(self, seconds):
            self.sleeps.append(seconds)
            self.seconds += seconds
            self.wall += timedelta(seconds=seconds)
        def advance(self, seconds):
            self.seconds += seconds
            self.wall += timedelta(seconds=seconds)
    clock = Clock()
    monkeypatch.setattr(campaign, 'now', lambda: clock.wall)
    monkeypatch.setattr(campaign.time, 'perf_counter', lambda: clock.seconds)
    monkeypatch.setattr(campaign.time, 'sleep', clock.sleep)
    monkeypatch.setattr(campaign, 'current_settings', lambda mode: settings)
    calls = []
    def stt(*a, **kw):
        calls.append(1); clock.advance(0.3); return speech()
    def llm(**kw):
        clock.advance(0.4); return feedback()
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', stt)
    monkeypatch.setattr(campaign, 'evaluate_interview_answer_llm', llm)
    original_write = campaign.atomic_json
    # Avoid hundreds of disk writes while virtual time advances through 4 hours.
    monkeypatch.setattr(campaign, 'atomic_json', lambda p, v: original_write(p, v) if p.name != 'runner.json' else None)
    directory = tmp_path / 'campaign'
    plan = campaign.create_plan(directory, settings, clock.wall, counts=(3, 3, 3))
    assert campaign.run_campaign(directory, wait=False) == 4
    assert len(calls) == 1
    assert campaign.run_campaign(directory, wait=True) == 0
    records = campaign.records_for(directory, plan)
    assert len(records) == len(calls) == 9
    assert max(clock.sleeps) <= 30
    first_finish = campaign.datetime.fromisoformat(records[2]['finished_at'])
    second_start = campaign.datetime.fromisoformat(records[3]['started_at'])
    assert (second_start - first_finish).total_seconds() == 7200
    assert campaign.read_json(directory / 'summary.json')['overall']['strict_latency_accepted']
    assert campaign.run_campaign(directory, wait=True) == 0 and len(calls) == 9


def test_interrupted_trial_retained_instead_of_rerun(tmp_path, settings, monkeypatch):
    directory = tmp_path / 'campaign'
    plan = campaign.create_plan(directory, settings, campaign.now(), counts=(3, 3, 3), interval=99999)
    record = {**plan['trials'][0], 'status': 'running', 'started_at': campaign.now().isoformat()}
    campaign.atomic_json(directory / 'trials/trial-001.json', record)
    monkeypatch.setattr(campaign, 'current_settings', lambda mode: settings)
    monkeypatch.setattr(campaign, 'transcribe_audio_whisper', lambda *a, **kw: pytest.fail('No early request'))
    assert campaign.run_campaign(directory, wait=False) == 4
    saved = campaign.read_json(directory / 'trials/trial-001.json')
    assert saved['status'] == 'interrupted'
    assert campaign.read_json(directory / 'summary.json')['overall']['errors'] == {'interrupted': 1}


def test_exclusive_runner_lock(tmp_path):
    with campaign.campaign_lock(tmp_path):
        with pytest.raises(campaign.CampaignError):
            with campaign.campaign_lock(tmp_path):
                pass
