# Task05 — AI Speech & LLM — Thiên Trường

Hai module chạy độc lập với FastAPI, database và FER: `backend/services/speech_service.py` bóc băng, lấy timestamps và đếm từ đệm; `backend/services/llm_service.py` nhận nội dung cùng dữ liệu FER để sinh JSON đánh giá. Các hàm trả `dict` có thể lưu JSON trực tiếp.

## Cài đặt

Dùng Python 3.11 trở lên; đã kiểm thử trên Windows với Python 3.12. Chạy các lệnh từ thư mục gốc repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Copy-Item .env.example .env
```

Nếu `.env` đã tồn tại, giữ file hiện có và bổ sung biến cần thiết. Điền `GROQ_API_KEY` và `GEMINI_API_KEY` trong `.env` để chạy thật. Trên Linux/macOS thay `.\.venv\Scripts\python.exe` bằng `.venv/bin/python`. Bản `imageio-ffmpeg` cho Windows/Linux/macOS thông dụng đi kèm FFmpeg; có thể chỉ định executable khác bằng `FFMPEG_BINARY`.

`backend/requirements-speech-llm.txt` chỉ chứa dependency của B để C có thể gộp vào requirements chung. Không cần PyTorch hoặc mô hình FER để chạy hai service này.

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `GROQ_API_KEY` | rỗng | Key dùng Groq Whisper Large V3 Turbo; tạo tại [Groq Console](https://console.groq.com/keys) |
| `GEMINI_API_KEY` | rỗng | Key dùng Gemini; có thể dùng `GOOGLE_API_KEY` nếu biến này rỗng |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Tên model Gemini, có thể đổi theo quyền truy cập của nhóm |
| `AI_MODE` | `live` | Service chạy thật hoặc `mock` |
| `AI_ALLOW_FALLBACK` | `true` | Trả dữ liệu mock có cờ khi lỗi mạng, HTTP 429 hoặc 5xx |
| `AI_TIMEOUT_SECONDS` | `20` | Timeout HTTP mỗi dịch vụ, không phải cam kết độ trễ |
| `FFMPEG_BINARY` | tự tìm | Đường dẫn executable FFmpeg |

CLI tự tải `.env`; khi C tích hợp, entry point backend cần gọi `load_dotenv()` hoặc cấu hình biến môi trường. Import module không tự đọc file hay khởi tạo API client.

## Chạy kiểm thử và demo

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m scripts.check_speech_llm tests/fixtures/interview_answer_en.webm --mode mock --output artifacts/speech-llm-demo.json
```

Demo thực sự giải mã file bằng FFmpeg, nhưng transcript/nhận xét là dữ liệu minh họa cố định. Transcript tiếng Việt trong chế độ mock không phải bản chép của audio tiếng Anh. `words` rỗng vì không có timestamps đo thật. Cờ `metadata.is_mock=true` xuất hiện ở cả hai kết quả; benchmark ghi `measured_live=false` và `target_met=null`.

Audio mẫu `tests/fixtures/interview_answer_en.webm` dài khoảng 22 giây, được tổng hợp cục bộ từ Windows SAPI. Nội dung nguồn là `tests/fixtures/interview_answer_en.txt`; không phải bản thu của một người thật. Có thể tạo lại WAV trên Windows bằng:

```powershell
./scripts/make_sample_audio.ps1
```

Chạy với API thật sau khi điền key:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_speech_llm tests/fixtures/interview_answer_en.webm --mode live --language en --question "Tell me about a difficult project problem you solved." --output artifacts/speech-llm-live.json
```

Thay đường dẫn bằng bản ghi tiếng Việt và dùng `--language vi` để kiểm tra từ đệm. Dùng `--language auto` nếu muốn Whisper tự nhận ngôn ngữ. `--fer-json path/to/fer.json` nhận kết quả thực tế của A. CLI không tự tạo điểm cảm xúc khi chưa có FER.

CLI mặc định tắt fallback để phép đo live không bị nhầm với kết quả demo. Có thể bật bằng `--allow-fallback`. Mã thoát: `0` chạy thành công; `1` lỗi cấu hình/đầu vào/API; `2` yêu cầu live nhưng phải trả mock hoặc không có lời nói để đánh giá; `3` vượt mục tiêu độ trễ khi bật `--enforce-latency`. `--max-seconds 3` là mục tiêu cho tổng thời gian tách audio + Whisper + LLM; báo cáo cũng chứa thời gian riêng từng service. Chỉ khi cả Whisper và Gemini đều thực sự trả kết quả mới đánh giá mục tiêu độ trễ. Chưa thể xác nhận tiêu chuẩn < 3 giây khi chưa chạy với API key thật.

## Hợp đồng Speech

```python
transcribe_audio_whisper(
    video_path,                    # đường dẫn WebM/MP4/WAV/MP3/M4A/OGG/FLAC/MPEG/MPGA
    language="vi",                # ISO-639-1 hoặc None
    settings=None,                # AISettings, mặc định đọc biến môi trường
    client=None,                  # Groq client tùy chọn; caller quản lý lifecycle
)
```

Kết quả ví dụ minh họa schema:

```json
{
  "transcript": "Ừm, tôi đã tối ưu truy vấn.",
  "words": [{"word": "Ừm,", "start": 0.0, "end": 0.3}],
  "duration_seconds": 2.5,
  "filler_words_count": 1,
  "filler_words": {"ừm": 1},
  "metadata": {
    "provider": "groq", "model": "whisper-large-v3-turbo", "is_mock": false,
    "fallback_reason": null, "latency_ms": 1200.0
  }
}
```

`words` trong ví dụ được rút gọn; khi chạy thật là danh sách timestamps nhà cung cấp trả về. Timestamps dùng đơn vị giây từ đầu audio và được kiểm tra không âm, đúng thứ tự, end >= start, không vượt quá thời lượng quá 0,5 giây.

FFmpeg chuyển audio sang WAV mono 16 kHz, PCM 16-bit. Giới hạn input 100 MiB, thời lượng mặc định tối đa 125 giây (câu hỏi 120 giây cộng khoảng đệm). Không cắt bỏ câu dài âm thầm: decoder đọc tối đa giới hạn + 1 giây rồi báo `invalid_duration` nếu vượt mức. Thời gian giải mã tối đa mặc định 30 giây. Có thể truyền `AISettings` để điều chỉnh các giới hạn.

`count_filler_words(text)` trả tổng số nguyên (giữ tương thích AI-01); `analyze_filler_words(text)` trả tổng và thống kê theo từng từ. Cả hai dùng Unicode NFC, không phân biệt hoa/thường, nhận `ừm`, `à`, `ờ`, `uhm`, `kiểu như`, `thì là`; giữ thêm các từ có sẵn trong AI-01: `um`, `dạ thì`, `kiểu là`. Khoảng trắng liên tiếp được chấp nhận trong cụm từ; các từ như `và`, `làm`, `giờ` không bị đếm nhầm theo ký tự con. Đây là đếm từ/cụm từ trong transcript: không xác định được tất cả trường hợp ngập ngừng thực sự, và Whisper có thể bỏ qua tiếng đệm. Muốn đo chất lượng cần đối chiếu các bản thu gán nhãn thủ công.

## Hợp đồng LLM

```python
evaluate_interview_answer_llm(
    question_text,
    transcript,
    confidence_score=None,        # tương thích tham số gốc của AI-01
    stress_score=None,
    filler_words_count=None,       # None: đếm từ transcript
    role_name="Software Engineer",
    emotion_metrics=None,          # keyword-only: dict kết quả FER của A
    speech_is_mock=False,          # bắt buộc truyền cờ từ STT khi ghép pipeline
    settings=None,
    client=None,                  # GenAI client tùy chọn; caller quản lý lifecycle
)
```

FER nhận các trường `confidence_score`, `stress_score` (0–100), `dominant_emotion`, `emotion_distribution` và `emotion_timeline`. Mỗi điểm timeline có `second`, `emotion` thuộc Happy/Normal/Sad/Surprised và `confidence` tùy chọn (0–1), `is_stress` tùy chọn như output hiện tại của A. Thiếu dữ liệu FER được giữ là null/rỗng, không biến thành điểm 0.

Output gồm `content_score` (0–100), `content_critique`, `delivery_critique`, `suggested_answer` và `metadata` cùng cấu trúc với Speech. Gemini bị ràng buộc JSON schema; Pydantic kiểm tra lần nữa, từ chối điểm ngoài khoảng, NaN, chuỗi giả số, trường thừa, nhận xét rỗng và JSON thiếu trường. Kết quả bị chặn/cắt ngắn cũng báo lỗi.

Prompt cho câu hỏi hành vi: Situation 15 + Task 15 + Action 40 + Result 30. Câu hỏi chuyên môn dùng độ đúng 50 + lập luận 30 + ví dụ 20. Quy tắc trọng số này là đề xuất triển khai của B vì tài liệu chỉ yêu cầu chấm STAR 0–100. Nhận xét phong thái tách khỏi điểm nội dung; không suy ra năng lực từ biểu cảm. Transcript được gửi ở phần user data riêng khỏi system prompt; cần tiếp tục thử nghiệm chất lượng prompt với câu trả lời thật ở tuần 2.

## Ghép với A và C

```python
from backend.services.speech_service import transcribe_audio_whisper
from backend.services.llm_service import evaluate_interview_answer_llm

speech = transcribe_audio_whisper(video_path)
feedback = evaluate_interview_answer_llm(
    transcript=speech["transcript"],
    question_text=question_text,
    role_name=role_name,
    emotion_metrics=fer_result,
    filler_words_count=speech["filler_words_count"],
    speech_is_mock=speech["metadata"]["is_mock"],
)
is_mock = speech["metadata"]["is_mock"] or feedback["metadata"]["is_mock"]
if is_mock:
    # Worker AI-01 lưu metadata, đặt câu thành FAILED và bỏ qua điểm mock khi tính summary.
    pass
```

Đây là các hàm **đồng bộ**, phù hợp sync BackgroundTasks/thread worker. Nếu worker là `async def`, C cần chạy hàm blocking trong threadpool. Hai service không quản lý DB. Worker của AI-01 đã được nối với các service và lưu word timestamps/provenance trong `ai_feedback`, không cần migration.

Speech tự xóa WAV và thư mục tạm nó tạo, kể cả khi API lỗi. Video đầu vào được giữ cho FER; pipeline của C chịu trách nhiệm xóa video gốc trong `finally` sau khi tất cả consumer dùng xong. Nếu inject client để tái sử dụng kết nối, caller chịu trách nhiệm đóng client; client do service tạo sẽ tự đóng.

Fallback chỉ dùng cho lỗi mạng/timeout, HTTP 429 hoặc 5xx. Speech fallback trả transcript/words rỗng; LLM fallback có nhãn `[MOCK]` và điểm 0 giữ chỗ. Khi truyền `speech_is_mock=True`, LLM không gọi API trên transcript giả. Thiếu key, HTTP 400/401/403/404, file lỗi hoặc response sai schema phát sinh `ServiceError` với `code` để C xử lý lỗi; không trả thành công giả. Lỗi lập trình ngoài dự kiến vẫn được ném ra để dễ phát hiện.

## Kiểm chứng

Test tự động không cần key và chặn kết nối mạng. Chúng kiểm tra Unicode/từ đệm, FFmpeg giải mã audio, cleanup khi lỗi, định dạng multipart Whisper và request Gemini qua SDK thật với HTTP transport giả lập, schema, lỗi mạng/API và việc truyền cờ mock giữa hai service. Dữ liệu audio tone sinh trong test chỉ kiểm tra đường xử lý media, không chứng minh chất lượng bóc băng. File giọng đọc tổng hợp dành cho demo và kiểm thử live thủ công.

Kết quả kiểm thử tự động và demo mock không thay thế kiểm thử chất lượng/độ trễ API thật. Đã cấu hình key ở máy và thử gọi live, nhưng API đang trả lỗi (chi tiết ở bảng nghiệm thu bên dưới). Cần chạy lại khi API hoạt động, sau đó thử thêm bản ghi tiếng Việt có từ đệm và đối chiếu transcript với nội dung đã gán nhãn.

## Tài liệu API đã đối chiếu

- [Groq Speech to Text](https://console.groq.com/docs/speech-to-text): dùng `whisper-large-v3-turbo`, `verbose_json`, `timestamp_granularities=["word"]` để lấy timestamps từng từ. API dùng key Groq, không dùng key OpenAI.
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/): `models.generate_content`, JSON schema, timeout và quản lý client.
- [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations): Gemini 2.0 đã dừng ngày 01/06/2026; cấu hình mặc định chuyển sang Gemini 3.8 Flash theo tài liệu ngày 09/10/2026. Quyền truy cập model thực tế cần kiểm chứng với key của nhóm.


## Đối chiếu thẻ Trello và trạng thái nghiệm thu

Nguồn: [Task05. AI Speech & LLM - Thiên Trường](https://trello.com/c/kRVKqM7d/7-task05-ai-speech-llm-thi%C3%AAn-tr%C6%B0%E1%BB%9Dng), đã đọc toàn bộ mô tả ngày 09/10/2026. Nhánh thực hiện: `feat/ai-speech-llm`, nền `AI-01` commit `bc2a8bb`.

| Yêu cầu | Kết quả và bằng chứng |
| --- | --- |
| Tách audio WebM, Groq Whisper STT + word timestamps | Đã code; test FFmpeg và HTTP contract của SDK đạt. Cần kiểm thử live với key Groq. |
| Regex đếm từ đệm | Đã code; test Unicode NFC/NFD, ranh giới từ và cụm nhiều khoảng trắng. |
| Gemini Flash + system prompt chuyên gia | Đã code, JSON schema và prompt kiểm tra bằng SDK HTTP giả lập. Live bị HTTP 503. |
| Transcript + cảm xúc + từ đệm → STAR, phong thái, câu mẫu | Đã code; test cả tham số gốc AI-01 và output thật của module analytics (inference FER được giả lập). |
| Fallback mock khi sự cố mạng | Đã kiểm thử timeout, 429, 5xx; metadata đánh dấu mock; worker không tính điểm giả. |
| Hàm và JSON chuẩn | Giữ tên và thứ tự tham số gốc của AI-01; bốn trường feedback + metadata mở rộng. |
| Kiểm thử độc lập, phản hồi < 3 giây | Có script và audio mẫu. Chưa đạt nghiệm thu live do API trả lỗi; không dùng độ trễ lỗi/mock làm bằng chứng. |
| Làm trên nhánh từ AI-01 và push GitHub | Code ở nhánh `feat/ai-speech-llm` trên máy; theo yêu cầu hiện tại chưa push thay đổi này. |

Lượt benchmark ngày 09/10/2026 dùng nhà cung cấp OpenAI cũ: Whisper trả HTTP 429 sau 2,731 giây; Gemini trả HTTP 503 sau 3,548 giây. Đây là **thời gian nhận lỗi**, không phải thời gian bóc băng/đánh giá thành công. Số liệu cũ không dùng để nghiệm thu Groq. Khi STT lỗi, Gemini được kiểm tra độc lập bằng văn bản nguồn của audio tổng hợp, không giả mạo đó là transcript Whisper. Báo cáo cục bộ ở `artifacts/live-benchmark.json` (được Git ignore).

Chạy lại phép đo độc lập:

```powershell
.\.venv\Scripts\python.exe -m scripts.benchmark_speech_llm
```

Script ghi kết quả từng dịch vụ dù một dịch vụ thất bại. `end_to_end.measured_live` chỉ true khi Groq và Gemini đều trả kết quả thật. Mỗi lần gọi SDK thực hiện một request với timeout, không retry vô hạn. HTTP 429 từ Groq cho biết đã chạm giới hạn yêu cầu; khi bật fallback, kết quả được đánh dấu mock.

Tích hợp AI-01: khi trả mock, câu được đánh dấu `FAILED`, metadata và nội dung demo vẫn có trong `ai_feedback` để xem xét, `content_score` trong DB là null. API results và worker loại các câu FAILED/mock khỏi trung bình. Session chuyển `FAILED` khi mọi câu đã kết thúc nhưng có câu thất bại, giúp polling dừng; câu thành công vẫn giữ kết quả. Lỗi cấu hình/schema được lưu bằng mã lỗi đã làm sạch, không đưa API key hoặc provider error body vào log/báo cáo.

Thư mục `docs/` là tài liệu nội bộ và bị ignore trên AI-01. Bản hướng dẫn đi kèm GitHub nằm tại `backend/SPEECH_LLM.md`.

Chạy lại `pytest` và benchmark sau khi cấu hình key Groq để kiểm chứng thay đổi nhà cung cấp và đo độ trễ thực tế.
