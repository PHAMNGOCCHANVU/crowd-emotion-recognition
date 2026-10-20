# Dockerfile cho Hugging Face Space (SDK Docker).
# Cấu trúc repo của Space: Dockerfile, README.md và thư mục backend/ (copy từ dự án).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face chạy container bằng user id 1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"
WORKDIR /home/user/app

COPY --chown=user backend/requirements.txt backend/requirements-speech-llm.txt ./backend/
RUN pip install --user -r backend/requirements.txt

COPY --chown=user backend/ ./backend/

EXPOSE 7860

# Import dạng backend.* nên chạy từ thư mục cha của backend/
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
