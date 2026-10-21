import subprocess
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import imageio_ffmpeg
import pytest
from groq import Groq

from backend.services.ai_contracts import AISettings, ServiceError, SpeechResult
from backend.services.speech_service import analyze_filler_words, count_filler_words, extracted_audio, transcribe_audio_whisper


@pytest.mark.parametrize(("text", "expected"), [
    ("Ừm, à, Ờ... UHM! kiểu như thì là", 6),
    ("và làm giờ nhà thường xuyên", 0),
    ("ừm ừm à à", 4),
    ("kiểu   như\nthì\tlà", 2),
    (unicodedata.normalize("NFD", "Ừm, kiểu như, à"), 3),
    ("", 0),
    ("uhmfoo foo_uhm uhm2", 0),
])
def test_filler_boundaries_and_unicode(text, expected):
    result = analyze_filler_words(text)
    assert count_filler_words(text) == expected
    assert result["filler_words_count"] == expected
    assert sum(result["filler_words"].values()) == expected


def whisper_client(handler):
    return Groq(api_key="test-key", max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def whisper_payload(**updates):
    return {
        "text": "Ừm, à.", "language": "vietnamese", "duration": 1.0,
        "words": [{"word": "Ừm,", "start": 0.0, "end": 0.3}, {"word": "à.", "start": 0.4, "end": 0.8}],
        **updates,
    }


def test_whisper_actual_sdk_multipart_and_result(sample_audio):
    def handler(request):
        assert request.url.path == "/openai/v1/audio/transcriptions"
        body = request.read()
        for part in (b"whisper-large-v3", b"verbose_json", b"timestamp_granularities[]", b"word", b"RIFF"):
            assert part in body
        return httpx.Response(200, json=whisper_payload())

    with whisper_client(handler) as client:
        result = transcribe_audio_whisper(sample_audio, settings=AISettings(), client=client)
        assert not client.is_closed()
    SpeechResult.model_validate(result)
    assert result["filler_words_count"] == 2
    assert result["words"][1]["start"] == 0.4
    assert result["metadata"]["provider"] == "groq"
    assert result["metadata"]["model"] == "whisper-large-v3"
    assert not result["metadata"]["is_mock"]
    assert sample_audio.exists()


@pytest.mark.parametrize("extension,codec", [("webm", "libopus"), ("mp4", "aac")])
def test_real_ffmpeg_container_conversion_and_cleanup(sample_audio, extension, codec):
    media = sample_audio.with_suffix("." + extension)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(sample_audio),
                    "-c:a", codec, str(media)], check=True, capture_output=True)
    with extracted_audio(media, AISettings()) as (audio, duration):
        assert audio.exists()
        assert duration == pytest.approx(1, abs=0.1)
        temporary = audio.parent
    assert not temporary.exists()
    assert media.exists()


@pytest.mark.parametrize("status", [429, 500, 503])
def test_transient_error_returns_flagged_empty_transcript(sample_audio, status):
    with whisper_client(lambda r: httpx.Response(status, json={"error": {"message": "unavailable"}})) as client:
        result = transcribe_audio_whisper(sample_audio, settings=AISettings(), client=client)
    assert result["transcript"] == ""
    assert result["words"] == []
    assert result["metadata"]["is_mock"]
    assert result["metadata"]["fallback_reason"] == "provider_unavailable"


@pytest.mark.parametrize("allow_fallback", [True, False])
def test_timeout_and_strict_mode(sample_audio, allow_fallback):
    def handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    with whisper_client(handler) as client:
        if allow_fallback:
            assert transcribe_audio_whisper(sample_audio, client=client)["metadata"]["is_mock"]
        else:
            with pytest.raises(ServiceError) as error:
                transcribe_audio_whisper(sample_audio, settings=AISettings(allow_fallback=False), client=client)
            assert error.value.code == "speech_unavailable"


@pytest.mark.parametrize("status", [400, 401, 403])
def test_auth_and_bad_request_do_not_become_fake_success(sample_audio, status):
    with whisper_client(lambda r: httpx.Response(status, json={"error": {"message": "secret-body"}})) as client:
        with pytest.raises(ServiceError) as error:
            transcribe_audio_whisper(sample_audio, client=client)
    assert error.value.code == "speech_api_error"
    assert "secret-body" not in str(error.value)


@pytest.mark.parametrize("updates", [
    {"words": []},
    {"words": [{"word": "a", "start": 0.6, "end": 0.2}]},
    {"words": [{"word": "a", "start": 0.0, "end": 10.0}]},
    {"words": [{"word": "a", "start": 0.5, "end": 0.7}, {"word": "b", "start": 0.1, "end": 0.2}]},
    {"text": None},
])
def test_invalid_provider_timestamps_rejected(sample_audio, updates):
    with whisper_client(lambda r: httpx.Response(200, json=whisper_payload(**updates))) as client:
        with pytest.raises(ServiceError) as error:
            transcribe_audio_whisper(sample_audio, client=client)
    assert error.value.code == "invalid_speech_response"


def test_empty_transcription_is_valid(sample_audio):
    with whisper_client(lambda r: httpx.Response(200, json=whisper_payload(text="", words=[]))) as client:
        result = transcribe_audio_whisper(sample_audio, client=client)
    assert result["transcript"] == ""
    assert not result["metadata"]["is_mock"]


def test_temp_audio_removed_on_unexpected_provider_failure(sample_audio):
    captured = []

    def fail(**kwargs):
        captured.append(Path(kwargs["file"].name))
        raise RuntimeError("unexpected SDK bug")

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=fail)))
    with pytest.raises(RuntimeError):
        transcribe_audio_whisper(sample_audio, client=client)
    assert not captured[0].exists()
    assert not captured[0].parent.exists()
    assert sample_audio.exists()


def test_bad_media_and_duration(sample_audio, tmp_path):
    with pytest.raises(ServiceError, match="thời lượng"):
        with extracted_audio(sample_audio, AISettings(max_duration_seconds=0.2)):
            pass
    broken = tmp_path / "broken.webm"
    broken.write_bytes(b"not media")
    with pytest.raises(ServiceError) as error:
        with extracted_audio(broken, AISettings()):
            pass
    assert error.value.code == "invalid_media"


def test_missing_key_is_actionable(sample_audio):
    with pytest.raises(ServiceError) as error:
        transcribe_audio_whisper(sample_audio)
    assert error.value.code == "missing_groq_key"


def test_mock_mode_no_api_or_invented_timestamps(sample_audio):
    client = Mock()
    result = transcribe_audio_whisper(sample_audio, settings=AISettings(mode="mock"), client=client)
    assert result["metadata"]["is_mock"]
    assert result["metadata"]["fallback_reason"] == "demo_mode"
    assert result["words"] == []
    assert result["filler_words_count"] == 2
    client.audio.transcriptions.create.assert_not_called()


def test_video_without_audio_is_rejected(tmp_path):
    video = tmp_path / "silent.mp4"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", "color=black:s=16x16:d=0.1", "-an", str(video)], check=True, capture_output=True)
    with pytest.raises(ServiceError) as error:
        with extracted_audio(video, AISettings()):
            pass
    assert error.value.code == "invalid_media"
    assert video.exists()


def test_extraction_timeout_cleans_partial_file(sample_audio, monkeypatch):
    generated = []

    def timeout(command, **kwargs):
        path = Path(command[-1])
        generated.append(path)
        path.write_bytes(b"partial wav")
        raise subprocess.TimeoutExpired(command, 30)

    monkeypatch.setattr("backend.services.speech_service.subprocess.run", timeout)
    with pytest.raises(ServiceError) as error:
        with extracted_audio(sample_audio, AISettings(ffmpeg_binary="test-ffmpeg")):
            pass
    assert error.value.code == "media_timeout"
    assert not generated[0].parent.exists()


def test_bundled_spoken_sample_decodes():
    sample = Path(__file__).parent / "fixtures" / "interview_answer_en.webm"
    with extracted_audio(sample, AISettings()) as (audio, duration):
        assert audio.is_file()
        assert 20 < duration < 25


@pytest.mark.parametrize("allow_fallback", [True, False])
def test_rate_limit_error_does_not_expose_provider_body(sample_audio, allow_fallback):
    with whisper_client(lambda r: httpx.Response(429, json={"error": {
        "message": "private provider detail", "type": "rate_limit_error",
    }})) as client:
        config = AISettings(allow_fallback=allow_fallback)
        if allow_fallback:
            result = transcribe_audio_whisper(sample_audio, settings=config, client=client)
            assert result["metadata"]["fallback_reason"] == "provider_unavailable"
        else:
            with pytest.raises(ServiceError) as error:
                transcribe_audio_whisper(sample_audio, settings=config, client=client)
            assert error.value.code == "speech_api_error"
            assert "private provider detail" not in str(error.value)
