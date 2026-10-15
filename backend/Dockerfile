# ==============================================================================
# Production Dockerfile for AI Mock Interview Backend
# Base: Python 3.12 Slim with FFmpeg & Headless OpenCV
# ==============================================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Cài đặt ffmpeg (đọc video WebM) và các thư viện hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt dependencies trước để tận dụng Docker layer cache
COPY requirements.txt requirements-speech-llm.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn backend
COPY . /app

EXPOSE 8000

# Chạy server Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
