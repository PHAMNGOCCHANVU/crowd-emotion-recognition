import math
import socket
import struct
import wave

import pytest


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "AI_MODE", "AI_ALLOW_FALLBACK",
                "AI_TIMEOUT_SECONDS", "GEMINI_MODEL", "FFMPEG_BINARY"):
        monkeypatch.delenv(key, raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("Offline tests must not access the network")

    monkeypatch.setattr(socket, "create_connection", no_network)


@pytest.fixture
def sample_audio(tmp_path):
    # A generated 1-second tone tests media decoding, NOT transcription accuracy.
    path = tmp_path / "câu trả lời.wav"
    samples = (int(5000 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(16000))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(struct.pack("<16000h", *samples))
    return path
