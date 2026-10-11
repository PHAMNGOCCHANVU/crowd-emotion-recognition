import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
from groq import Groq
import pytest

from backend.services.ai_contracts import AISettings
from backend.services.llm_service import evaluate_interview_answer_llm
from backend.services.speech_service import transcribe_audio_whisper


def test_whisper_outage_propagates_mock_to_evaluator(sample_audio):
    with Groq(api_key="test", max_retries=0, http_client=httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(503, json={"error": {"message": "offline"}})),
    )) as client:
        speech = transcribe_audio_whisper(sample_audio, client=client)
    feedback = evaluate_interview_answer_llm(
        transcript=speech["transcript"], question_text="Question?", role_name="Engineer", filler_words_count=speech["filler_words_count"],
        speech_is_mock=speech["metadata"]["is_mock"], settings=AISettings(),
    )
    assert speech["metadata"]["is_mock"] and feedback["metadata"]["is_mock"]
    assert feedback["metadata"]["fallback_reason"] == "mock_speech"


def test_cli_mock_report_does_not_claim_live_latency(sample_audio, tmp_path):
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, "-m", "scripts.check_speech_llm", str(sample_audio), "--mode", "mock", "--output", str(report_path)],
        cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONUTF8": "1"},
        capture_output=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["speech"]["filler_words_count"] == 2
    assert report["benchmark"]["measured_live"] is False
    assert report["benchmark"]["target_met"] is None


def test_cli_empty_transcript_does_not_pass_live_benchmark(monkeypatch, capsys):
    from scripts import check_speech_llm as cli

    monkeypatch.setattr(sys, "argv", ["check", "unused.wav", "--mode", "live"])
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **kw: None)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(cli, "transcribe_audio_whisper", lambda *a, **kw: {
        "transcript": "", "filler_words_count": 0,
        "metadata": {"provider": "groq", "is_mock": False},
    })
    # Empty speech is evaluated locally, so a fast result must not pass the API SLA.
    assert cli.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["feedback"]["metadata"]["provider"] == "local"
    assert report["benchmark"]["measured_live"] is False
    assert report["benchmark"]["target_met"] is None


def test_cli_missing_keys_reports_actionable_error(monkeypatch, capsys):
    from scripts import check_speech_llm as cli

    monkeypatch.setattr(sys, "argv", ["check", "unused.wav", "--mode", "live"])
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **kw: None)
    assert cli.main() == 1
    assert json.loads(capsys.readouterr().err)["error"] == "missing_api_keys"


@pytest.mark.parametrize("speech_ok", [True, False])
def test_benchmark_distinguishes_reference_text_from_transcription(monkeypatch, tmp_path, capsys, speech_ok):
    from scripts import benchmark_speech_llm as cli
    from backend.services.ai_contracts import ServiceError

    output = tmp_path / "benchmark.json"
    monkeypatch.setattr(sys, "argv", ["benchmark", "--output", str(output)])
    monkeypatch.setattr(cli, "load_dotenv", lambda *a, **kw: None)

    def speech(*args, **kwargs):
        if not speech_ok:
            raise ServiceError("speech_api_error", "Whisper HTTP 429")
        return {"transcript": "actual transcript", "metadata": {"provider": "groq"}}

    monkeypatch.setattr(cli, "transcribe_audio_whisper", speech)
    monkeypatch.setattr(cli, "evaluate_interview_answer_llm", lambda **kwargs: {
        "metadata": {"provider": "gemini"}, "input_for_test": kwargs["transcript"],
    })
    assert cli.main() == (0 if speech_ok else 1)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["end_to_end"]["measured_live"] is speech_ok
    if not speech_ok:
        assert report["end_to_end"]["target_met"] is None
        assert report["llm_input_source"] == "reference_text_not_transcription"
    else:
        assert report["llm"]["result"]["input_for_test"] == "actual transcript"
