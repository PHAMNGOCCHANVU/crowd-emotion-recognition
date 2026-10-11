"""Run member B's services against one media file, with explicit live/mock mode."""

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from backend.services.ai_contracts import AISettings, ServiceError
from backend.services.llm_service import evaluate_interview_answer_llm
from backend.services.speech_service import transcribe_audio_whisper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("media", type=Path, help="Local WebM/MP4/WAV/audio file")
    parser.add_argument("--mode", choices=["live", "mock"], default="live")
    parser.add_argument("--language", default="vi", help="vi, en, or auto")
    parser.add_argument("--question", default="Kể về một lần bạn giải quyết vấn đề khó trong dự án.")
    parser.add_argument("--role", default="Software Engineer")
    parser.add_argument("--fer-json", type=Path, help="Optional FER metrics JSON from member A")
    parser.add_argument("--allow-fallback", action="store_true", help="Allow flagged mock data on transient errors")
    parser.add_argument("--max-seconds", type=float, default=3.0, help="Target for STT + LLM combined")
    parser.add_argument("--enforce-latency", action="store_true", help="Exit 3 if real run exceeds the target")
    parser.add_argument("--output", type=Path, help="Optional JSON report (contains transcript)")
    args = parser.parse_args()
    if args.max_seconds <= 0:
        parser.error("--max-seconds must be positive")
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    started = time.perf_counter()
    try:
        config = AISettings.from_env().model_copy(update={
            "mode": args.mode, "allow_fallback": args.allow_fallback,
        })
        if args.mode == "live" and (not config.groq_api_key or not config.gemini_api_key):
            raise ServiceError("missing_api_keys", "Điền GROQ_API_KEY và GEMINI_API_KEY trong .env trước khi chạy live.")
        fer = json.loads(args.fer_json.read_text(encoding="utf-8")) if args.fer_json else None
        speech = transcribe_audio_whisper(
            args.media, language=None if args.language == "auto" else args.language, settings=config,
        )
        feedback = evaluate_interview_answer_llm(
            transcript=speech["transcript"], question_text=args.question, role_name=args.role,
            emotion_metrics=fer, filler_words_count=speech["filler_words_count"],
            speech_is_mock=speech["metadata"]["is_mock"], settings=config,
        )
    except (ServiceError, ValidationError, OSError, ValueError) as exc:
        # Do not print provider exception bodies, env values, or Pydantic input dumps.
        code = exc.code if isinstance(exc, ServiceError) else "invalid_configuration_or_input"
        message = str(exc) if isinstance(exc, ServiceError) else "Kiểm tra cấu hình và đường dẫn/JSON đầu vào."
        print(json.dumps({"error": code, "message": message}, ensure_ascii=False), file=sys.stderr)
        return 1
    elapsed = round(time.perf_counter() - started, 3)
    real = (speech["metadata"]["provider"] == "groq"
            and feedback["metadata"]["provider"] == "gemini")
    report = {
        "mode": args.mode, "speech": speech, "feedback": feedback,
        "benchmark": {"total_seconds": elapsed, "target_seconds": args.max_seconds,
                      "measured_live": real, "target_met": elapsed < args.max_seconds if real else None},
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    if args.mode == "live" and not real:
        return 2
    if args.enforce_latency and real and elapsed >= args.max_seconds:
        return 3
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
