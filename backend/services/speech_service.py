"""Decode one interview answer, transcribe with Whisper, and count fillers."""

import re
import subprocess
import tempfile
import time
import unicodedata
import wave
from collections import Counter
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Iterator

import imageio_ffmpeg
from groq import APIConnectionError, APIStatusError, Groq
from pydantic import ValidationError

from .ai_contracts import AISettings, ServiceError, ServiceMetadata, SpeechResult, WordTimestamp

FILLERS = ("kiểu như", "thì là", "dạ thì", "kiểu là", "ừm", "à", "ờ", "uhm", "um")
# Unicode boundaries avoid matching 'à' in 'và'/'làm' or 'ờ' in 'giờ'.
_FILLER_PATTERN = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(s).replace(r"\ ", r"\s+") for s in FILLERS) + r")(?!\w)",
    re.IGNORECASE,
)
SUPPORTED_EXTENSIONS = {".wav", ".webm", ".mp4", ".m4a", ".mp3", ".ogg", ".flac", ".mpeg", ".mpga"}
DEMO_TRANSCRIPT = "Ừm, tôi phụ trách backend. À, tôi đã tối ưu truy vấn và giảm thời gian phản hồi."
SPEECH_MODEL = "whisper-large-v3"


def analyze_filler_words(transcript: str) -> dict:
    """Count lexical occurrences, not an acoustic/semantic hesitation diagnosis."""
    normalized = unicodedata.normalize("NFC", transcript)
    counts = Counter(" ".join(m.group().lower().split()) for m in _FILLER_PATTERN.finditer(normalized))
    return {"filler_words_count": sum(counts.values()), "filler_words": dict(counts)}


def count_filler_words(text: str) -> int:
    """Keep the original AI-01 helper's integer return contract."""
    return analyze_filler_words(text)["filler_words_count"]


@contextmanager
def extracted_audio(media_path: str | Path, settings: AISettings) -> Iterator[tuple[Path, float]]:
    """Own only the generated WAV; leave the input video for FER/the worker."""
    source = Path(media_path).resolve()
    if not source.is_file():
        raise ServiceError("invalid_media", "Không tìm thấy file audio/video.")
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS or source.stat().st_size == 0:
        raise ServiceError("invalid_media", "Định dạng không hỗ trợ hoặc file rỗng.")
    if source.stat().st_size > 100 * 1024 * 1024:
        raise ServiceError("invalid_media", "File đầu vào vượt giới hạn 100 MiB cho một câu.")
    try:
        binary = settings.ffmpeg_binary or imageio_ffmpeg.get_ffmpeg_exe()
    except RuntimeError as exc:
        raise ServiceError("ffmpeg_unavailable", "Chưa tìm thấy FFmpeg; kiểm tra FFMPEG_BINARY.") from exc

    with tempfile.TemporaryDirectory(prefix="interview-speech-") as tmp:
        target = Path(tmp) / "audio.wav"
        command = [
            binary, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
            # Decode one extra second to reject oversize answers without unbounded disk use.
            "-t", str(settings.max_duration_seconds + 1), "-c:a", "pcm_s16le", str(target),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=settings.extraction_timeout_seconds)
        except FileNotFoundError as exc:
            raise ServiceError("ffmpeg_unavailable", "Không chạy được FFmpeg.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ServiceError("media_timeout", "Tách audio vượt thời gian cho phép.") from exc
        except subprocess.CalledProcessError as exc:
            raise ServiceError("invalid_media", "File hỏng hoặc không có luồng âm thanh.") from exc
        try:
            with wave.open(str(target), "rb") as wav:
                duration = wav.getnframes() / wav.getframerate()
        except (OSError, EOFError, wave.Error) as exc:
            raise ServiceError("invalid_media", "Không đọc được audio đã tách.") from exc
        if duration <= 0 or duration > settings.max_duration_seconds:
            raise ServiceError("invalid_duration", "Câu trả lời rỗng hoặc vượt giới hạn thời lượng.")
        if target.stat().st_size >= 25_000_000:
            raise ServiceError("invalid_media", "Audio vượt giới hạn upload Whisper.")
        yield target, duration


def transcribe_audio_whisper(
    video_path: str | Path,
    *,
    language: str | None = "vi",
    settings: AISettings | None = None,
    client=None,
) -> dict:
    """Sync function for a worker/thread; returns a JSON-serializable SpeechResult.

    An injected Groq client is caller-owned (also useful for tests).
    Network/429/5xx failures may return a flagged, EMPTY fallback transcript.
    Missing keys, invalid files, auth errors, and malformed replies raise ServiceError.
    """
    started = time.perf_counter()
    settings = settings or AISettings.from_env()
    if language is not None and not re.fullmatch(r"[a-z]{2}", language):
        raise ServiceError("invalid_language", "language phải là mã ISO-639-1 hoặc None.")
    if settings.mode == "live" and client is None and not settings.groq_api_key:
        raise ServiceError("missing_groq_key", "Cần GROQ_API_KEY để chạy Groq Whisper thật.")

    with extracted_audio(video_path, settings) as (audio_path, duration):
        if settings.mode == "mock":
            return _result(DEMO_TRANSCRIPT, [], duration, started, "mock", "demo_mode", language)
        provider = client if client is not None else Groq(
            api_key=settings.groq_api_key.get_secret_value(),
            timeout=settings.timeout_seconds, max_retries=0,
        )
        try:
            with (nullcontext(provider) if client is not None else provider) as api:
                with audio_path.open("rb") as audio:
                    response = api.audio.transcriptions.create(
                        model=SPEECH_MODEL, file=audio, response_format="verbose_json",
                        timestamp_granularities=["word"],
                        **({"language": language} if language else {}),
                    )
        except APIConnectionError as exc:
            if settings.allow_fallback:
                return _result("", [], duration, started, "mock", "provider_unavailable", language)
            raise ServiceError("speech_unavailable", "Không kết nối được Whisper.") from exc
        except APIStatusError as exc:
            transient = exc.status_code == 429 or exc.status_code >= 500
            if transient and settings.allow_fallback:
                return _result("", [], duration, started, "mock", "provider_unavailable", language)
            raise ServiceError("speech_api_error", f"Groq Whisper trả HTTP {exc.status_code}.") from exc

        try:
            if not isinstance(response.text, str):
                raise ValueError("missing transcript")
            text = response.text.strip()
            words = [WordTimestamp.model_validate(w.model_dump() if hasattr(w, "model_dump") else w)
                     for w in (getattr(response, "words", None) or [])]
            if text and not words:
                raise ValueError("missing word timestamps")
            if not text and words:
                raise ValueError("timestamps without transcript")
            if any(w.end > duration + 0.5 for w in words):
                raise ValueError("timestamps exceed audio")
            if any(b.start < a.start for a, b in zip(words, words[1:])):
                raise ValueError("timestamps out of order")
        except (AttributeError, TypeError, ValueError, ValidationError) as exc:
            raise ServiceError("invalid_speech_response", "Whisper trả transcript/timestamps không hợp lệ.") from exc
        return _result(text, words, duration, started, "groq", None, getattr(response, "language", language))


def _result(text, words, duration, started, provider, reason, language) -> dict:
    return SpeechResult(
        transcript=text, words=words, duration_seconds=duration, language=language,
        **analyze_filler_words(text),
        metadata=ServiceMetadata(
            provider=provider, model=SPEECH_MODEL if provider == "groq" else None,
            is_mock=provider == "mock", fallback_reason=reason,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        ),
    ).model_dump(mode="json")
