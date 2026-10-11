"""Measure real services independently; preserve failures without exposing keys."""

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

ROOT = Path(__file__).resolve().parents[1]


def measure(operation):
    started = time.perf_counter()
    try:
        result = operation()
        return {"status": "ok", "seconds": round(time.perf_counter() - started, 3), "result": result}
    except ServiceError as exc:
        return {"status": "error", "seconds": round(time.perf_counter() - started, 3),
                "error": exc.code, "message": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, default=ROOT / "tests/fixtures/interview_answer_en.webm")
    parser.add_argument("--reference", type=Path, default=ROOT / "tests/fixtures/interview_answer_en.txt")
    parser.add_argument("--language", default="en")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/live-benchmark.json")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    try:
        config = AISettings.from_env().model_copy(update={"mode": "live", "allow_fallback": False})
        reference = args.reference.read_text(encoding="utf-8")
    except (OSError, ValidationError):
        print("Invalid configuration or reference file.", file=sys.stderr)
        return 1
    speech = measure(lambda: transcribe_audio_whisper(args.media, language=args.language, settings=config))
    transcript = speech["result"]["transcript"] if speech["status"] == "ok" else reference
    llm = measure(lambda: evaluate_interview_answer_llm(
        question_text="Tell me about a difficult project problem you solved.",
        transcript=transcript, role_name="Software Engineer", settings=config,
    ))
    complete = (speech["status"] == llm["status"] == "ok"
                and speech["result"]["metadata"]["provider"] == "groq"
                and llm["result"]["metadata"]["provider"] == "gemini")
    elapsed = round(speech["seconds"] + llm["seconds"], 3) if complete else None
    report = {
        "speech": speech, "llm": llm,
        "llm_input_source": "whisper_transcript" if speech["status"] == "ok" else "reference_text_not_transcription",
        "end_to_end": {"measured_live": complete, "total_seconds": elapsed,
                       "target_seconds": 3, "target_met": elapsed < 3 if complete else None},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Summary does not expose provider error bodies, credentials, or audio content.
    print(json.dumps({"speech": {k: v for k, v in speech.items() if k != "result"},
                      "llm": {k: v for k, v in llm.items() if k != "result"},
                      "end_to_end": report["end_to_end"]}, ensure_ascii=False, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
