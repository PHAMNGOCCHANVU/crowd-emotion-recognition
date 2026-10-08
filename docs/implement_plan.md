# BẢN ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS) & BẢN THIẾT KẾ KỸ THUẬT DỰ ÁN
## ĐỀ TÀI: NỀN TẢNG LUYỆN PHỎNG VẤN THỬ THÔNG MINH TÍCH HỢP AI ĐA PHƯƠNG THỨC (AI MOCK INTERVIEW PLATFORM)
### *Bước phát triển ứng dụng thực tiễn từ Codebase Nhận diện Cảm xúc (Emotion Recognition)*

---

## 🧭 PHẦN 1: BÀI TOÁN "ĐỂ LÀM GÌ?" & BẢN ĐỒ CHUYỂN DỊCH CODEBASE

### 1.1. Trả lời câu hỏi cốt lõi: "Nhận diện cảm xúc ĐỂ LÀM GÌ?"
Trong các đồ án công nghệ, mô hình nhận diện biểu cảm khuôn mặt (Facial Emotion Recognition - FER) đơn thuần sẽ lập tức vấp phải câu hỏi từ hội đồng: **"Mô hình nhận diện cảm xúc này sinh ra để làm gì? Ứng dụng thực tiễn ở đâu?"** Nếu chỉ dừng lại ở việc đếm số người và hiển thị % Vui/Buồn/Bình thường, hệ thống chỉ dừng lại ở một bài tập thị giác máy tính thô (Raw Computer Vision capability).

**Lời giải ứng dụng thực tiễn:**
Chuyển hóa toàn bộ năng lực nhận diện cảm xúc từ codebase hiện tại thành **Trục Đánh Giá Phong Thái (Non-verbal Evaluation Engine)** cốt lõi trong **Nền tảng Luyện Phỏng Vấn Thử Thông Minh (AI Mock Interview)**:
1. **Phỏng vấn tuyển dụng là bài toán Đa phương thức (Multimodal):**
   - Nhà tuyển dụng luôn đánh giá ứng viên dựa trên 2 yếu tố song hành: **Nội dung (Verbal)** (trả lời đúng chuyên môn, cấu trúc logic) và **Phong thái (Non-verbal)** (độ tự tin, sự điềm tĩnh, mức độ căng thẳng, kiểm soát nét mặt).
2. **Giá trị độc bản của mô hình Cảm xúc trong bài toán này:**
   - Mô hình AI cảm xúc từ codebase hiện tại đóng vai trò bóc tách biểu cảm vi mô theo từng giây trong câu trả lời của ứng viên:
     - Tính toán **Chỉ số Tự tin (Confidence Score)** dựa trên tỷ lệ biểu cảm tích cực (`Happy`) và phong thái bình thản (`Normal`).
     - Tính toán **Mức độ Căng thẳng (Stress/Hesitation Score)** khi ứng viên biểu lộ sự bối rối, nhăn nhó, sợ hãi (`Sad`/`Surprised`) trước các câu hỏi khó.
     - Vẽ **Biểu đồ Dòng thời gian Cảm xúc (Emotion Timeline)** đồng bộ theo video để chỉ ra chính xác: *"Ở giây thứ 45, khi gặp câu hỏi về thuật toán, nét mặt của bạn trở nên căng thẳng đột biến"*.
3. **Sức mạnh kết hợp Đa phương thức (Multimodal Synergy):**
   - **Thị giác (Codebase hiện tại):** Đánh giá phong thái khuôn mặt qua ResNet-18.
   - **Giọng nói (Whisper API):** Chuyển lời nói thành văn bản, bắt lỗi từ ngập ngừng ("ừm", "à").
   - **Tư duy & Chuyên môn (Google Gemini API):** Tổng hợp cả nội dung lời nói và dữ liệu phong thái để đưa ra nhận xét chuyên sâu toàn diện.

---

### 1.2. Chốt Công Nghệ Phát Triển (Finalized Tech Stack)

Hệ thống được chốt các công nghệ tối ưu nhất theo nguyên tắc **KISS (Keep It Simple, Stupid)**, hiệu năng cao và triển khai nhanh trong 2 tuần:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BẢNG CHỐT CÔNG NGHỆ DỰ ÁN                              │
├─────────────────────┬───────────────────────────┬──────────────────────────────────────┤
│ Tầng Kiến trúc      │ Công nghệ lựa chọn        │ Lý do chốt lựa chọn                  │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Frontend            │ React + Vite (SPA)        │ Xây dựng giao diện mượt mà, hỗ trợ   │
│                     │ CSS: Vanilla / Tailwind   │ tối đa MediaRecorder API, quản lý    │
│                     │ Charts: Recharts/Chart.js │ Blob URL trong RAM, vẽ Timeline đẹp. │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Backend API         │ Python FastAPI            │ Đồng bộ với AI Python, tích hợp sẵn  │
│                     │ Uvicorn ASGI Server       │ BackgroundTasks (in-process async),  │
│                     │ Pydantic Validation       │ tự sinh Swagger UI tương tác nhanh.  │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Cơ sở dữ liệu       │ SQLite (file interview.db)│ Tinh gọn, không cần cấu hình server  │
│                     │ SQLAlchemy ORM            │ riêng, chỉ lưu Text/JSON điểm số.    │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ AI - Non-verbal     │ PyTorch + OpenCV          │ TÁI SỬ DỤNG trực tiếp từ codebase:   │
│ (Thị giác/Cảm xúc)  │ ResNet-18 Backbone        │ weights/crowd_emotion_resnet18.pt,   │
│                     │ Face Detector (Webcam)    │ phân loại 4 nhãn (Happy, Normal, Sad,│
│                     │                           │ Surprised) tính Confidence & Stress. │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ AI - Verbal         │ OpenAI Whisper API        │ Tốc độ xử lý siêu nhanh (< 2s), nhận │
│ (Giọng nói/STT)     │ (audio/transcriptions)    │ diện tiếng Việt & tiếng Anh xuất sắc,│
│                     │                           │ trích xuất timestamps từng từ.       │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ AI - Cognitive      │ Google Gemini 1.5/2.0     │ Tốc độ cực nhanh, miễn phí hạn mức   │
│ (Đánh giá chuyên môn│ Flash API                 │ cao, hỗ trợ Structured JSON Output để│
│ & Sinh nhận xét)    │                           │ chấm điểm STAR và nhận xét đa chiều. │
├─────────────────────┼───────────────────────────┼──────────────────────────────────────┤
│ Cơ chế lưu trữ      │ Ephemeral Storage (/tmp/) │ Không dùng S3/Cloud Storage đắt đỏ:  │
│ Video tạm           │ Client Blob RAM Replay    │ Server xóa file ngay sau trích xuất; │
│                     │                           │ Client phát lại video từ RAM Blob URL│
└─────────────────────┴───────────────────────────┴──────────────────────────────────────┘
```

---

### 1.3. Chốt Thay Đổi Cấu Trúc Thư Mục Source Code (Directory Structure Migration)

Toàn bộ project được tái cấu trúc thành mô hình **Monorepo phân tầng sạch sẽ (Decoupled Monorepo)**:

#### Cấu trúc Thư mục Mới Chuẩn hóa:
```
d:\emotion_recognition\
├── 📂 backend/                      ← BACKEND FASTAPI CHÍNH
│   ├── main.py                      ← Khởi tạo app FastAPI, CORS, routers
│   ├── database.py                  ← Cấu hình SQLite engine & session
│   ├── models.py                    ← SQLAlchemy models (Users, Sessions, Details)
│   ├── schemas.py                   ← Pydantic schemas (Request/Response DTO)
│   ├── requirements.txt             ← Thư viện backend (fastapi, uvicorn, openai, google-genai...)
│   ├── 📂 api/                      ← Router endpoints
│   │   ├── __init__.py
│   │   ├── sessions.py              ← API tạo phiên, nộp video, xem kết quả
│   │   └── questions.py             ← API lấy ngân hàng câu hỏi theo ngành
│   └── 📂 services/                 ← Nghiệp vụ xử lý
│       ├── __init__.py
│       ├── fer_service.py           ← Gọi mô hình ResNet-18 từ ai_core/
│       ├── speech_service.py        ← Tách audio, gọi Whisper API, đếm filler words
│       ├── llm_service.py           ← Gọi Gemini API chấm điểm & sinh nhận xét
│       └── pipeline_worker.py       ← Điều phối BackgroundTasks & xóa file /tmp/
│
├── 📂 frontend/                     ← FRONTEND REACT + VITE (SPA)
│   ├── package.json                 ← Cấu hình dependencies (react, recharts, axios, lucide-react)
│   ├── vite.config.js               ← Cấu hình Vite & proxy sang backend (:8000)
│   ├── index.html                   ← HTML root template
│   └── 📂 src/
│       ├── App.jsx                  ← Định tuyến (React Router: /, /interview, /dashboard)
│       ├── main.jsx                 ← Entry point React
│       ├── 📂 pages/
│       │   ├── SetupPage.jsx        ← Chọn ngành/JD & Kiểm tra Webcam/Microphone
│       │   ├── InterviewRoom.jsx    ← Phòng phỏng vấn, đếm ngược, MediaRecorder, Blob RAM
│       │   └── DashboardPage.jsx    ← Thẻ điểm tổng thể, Timeline cảm xúc, Video Blob replay
│       ├── 📂 components/           ← Các widget giao diện tái sử dụng
│       │   ├── VideoPreview.jsx     ← Khung hiển thị camera & video phát lại
│       │   ├── EmotionChart.jsx     ← Biểu đồ đường Timeline cảm xúc theo giây
│       │   ├── ScoreCard.jsx        ← Thẻ điểm Radar / Circle score
│       │   └── FeedbackAccordion.jsx← Khung nhận xét chi tiết và gợi ý câu trả lời
│       └── 📂 services/
│           └── api.js               ← Axios client kết nối các endpoint Backend
│
├── 📂 ai_core/                      ← KẾ THỪA TRỰC TIẾP TỪ CODEBASE HIỆN TẠI
│   ├── __init__.py
│   ├── crowd_emotion_model.py       ← Kiến trúc mô hình ResNet-18 (4 nhãn)
│   ├── face_detector.py             ← Bắt khuôn mặt chính diện của ứng viên
│   └── interview_analytics.py       ← Refactor từ crowd_analytics.py: tính Confidence/Stress/Timeline
│
├── 📂 weights/                      ← FILE TRỌNG SỐ MÔ HÌNH
│   ├── crowd_emotion_resnet18.pt    ← Trọng số mô hình cảm xúc 4 nhãn đã huấn luyện
│   └── yolov8n-face.pt              ← Trọng số mô hình detector
│
├── 📂 legacy_crowd/                 ← LƯU TRỮ TOÀN BỘ CODE GIÁM SÁT CCTV CŨ (GIỮ LỊCH SỬ)
│   ├── app.py                       ← Streamlit dashboard cũ
│   ├── video_stream.py              ← Pipeline stream CCTV cũ
│   ├── alert_engine.py              ← Bộ cảnh báo an ninh cũ
│   ├── test_pipeline.py             ← Script test cũ
│   └── live_emotion_recognition.py  ← Code demo cũ của tác giả
│
└── 📂 docs/                         ← TÀI LIỆU DỰ ÁN
    └── SRS.md                       ← Bản đặc tả hoàn thiện (File này)
```

---

## 🔌 PHẦN 2: CHỐT THIẾT KẾ API CHI TIẾT (FINALIZED API CONTRACTS)

Hệ thống giao tiếp thông qua **RESTful API** chuẩn JSON giữa Frontend React và Backend FastAPI.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             DANH SÁCH ENDPOINTS CHÍNH                                  │
├─────────────────┬────────────────────────────────────────────┬─────────────────────────┤
│ Phương thức     │ Đường dẫn Endpoint                         │ Chức năng chính         │
├─────────────────┼────────────────────────────────────────────┼─────────────────────────┤
│ POST            │ /api/sessions/start                        │ Khởi tạo phiên phỏng vấn│
│ POST            │ /api/sessions/{session_id}/questions/{q}/ans│ Nộp video câu trả lời   │
│ GET             │ /api/sessions/{session_id}/status          │ Polling tiến độ xử lý   │
│ GET             │ /api/sessions/{session_id}/results         │ Lấy toàn bộ kết quả     │
└─────────────────┴────────────────────────────────────────────┴─────────────────────────┘
```

### 2.1. API Khởi tạo Phiên phỏng vấn
- **Endpoint:** `POST /api/sessions/start`
- **Request Body (JSON):**
  ```json
  {
    "user_id": "usr_98234",
    "role_name": "Software Engineer",
    "jd_text": "Tuyển dụng lập trình viên Python/FastAPI, có kinh nghiệm làm việc nhóm, nắm vững cấu trúc dữ liệu và giải thuật."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "session_id": "ses_550e8400-e29b-41d4-a716-446655440000",
    "role_name": "Software Engineer",
    "total_questions": 3,
    "questions": [
      {
        "order_index": 1,
        "question_text": "Bạn hãy giới thiệu bản thân và dự án công nghệ ấn tượng nhất mà bạn từng tham gia?",
        "time_limit_seconds": 120
      },
      {
        "order_index": 2,
        "question_text": "Hãy giải thích cách bạn xử lý xung đột ý kiến kỹ thuật khi làm việc nhóm?",
        "time_limit_seconds": 120
      },
      {
        "order_index": 3,
        "question_text": "Theo bạn, điểm khác biệt giữa tiến trình bất đồng bộ (Async) và đa luồng (Multithreading) trong Python là gì?",
        "time_limit_seconds": 120
      }
    ],
    "created_at": "2026-10-09T08:30:00Z"
  }
  ```

---

### 2.2. API Nộp Video Câu trả lời (Upload & Background Task)
- **Endpoint:** `POST /api/sessions/{session_id}/questions/{order_index}/answer`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `video_file`: File nhị phân WebM/MP4 được ghi từ `MediaRecorder`.
- **Cơ chế xử lý:**
  1. Backend ghi file tạm vào `/tmp/{session_id}_q{order_index}.webm`.
  2. Bắn tác vụ nền `BackgroundTasks(process_answer_pipeline, session_id, order_index, temp_path)`.
  3. Lập tức trả về mã `202 Accepted` cho Frontend trong vòng **$< 800$ms**.
- **Response (202 Accepted):**
  ```json
  {
    "status": "PROCESSING",
    "message": "Video câu 1 đã được tiếp nhận và đang phân tích ngầm.",
    "session_id": "ses_550e8400-e29b-41d4-a716-446655440000",
    "order_index": 1
  }
  ```

---

### 2.3. API Kiểm tra Tiến độ (Status Polling)
- **Endpoint:** `GET /api/sessions/{session_id}/status`
- **Response (200 OK):**
  ```json
  {
    "session_id": "ses_550e8400-e29b-41d4-a716-446655440000",
    "overall_status": "PROCESSING",
    "questions": [
      {"order_index": 1, "status": "COMPLETED"},
      {"order_index": 2, "status": "COMPLETED"},
      {"order_index": 3, "status": "PROCESSING"}
    ],
    "is_fully_completed": false
  }
  ```

---

### 2.4. API Lấy Kết Quả Đa Phương Thức Toàn Phiên (Full Results)
- **Endpoint:** `GET /api/sessions/{session_id}/results`
- **Response (200 OK):**
  ```json
  {
    "session_id": "ses_550e8400-e29b-41d4-a716-446655440000",
    "role_name": "Software Engineer",
    "summary": {
      "overall_score": 84.5,
      "content_score_avg": 86.0,
      "confidence_score_avg": 82.0,
      "stress_score_avg": 18.0,
      "total_filler_words": 5,
      "final_verdict": "Ứng viên có kiến thức chuyên môn vững vàng, phong thái điềm tĩnh, cần giảm bớt từ đệm ở câu hỏi lý thuyết."
    },
    "details": [
      {
        "order_index": 1,
        "question_text": "Bạn hãy giới thiệu bản thân và dự án công nghệ ấn tượng nhất mà bạn từng tham gia?",
        "transcript": "Xin chào, tôi là một kỹ sư phần mềm chuyên về Backend. Dự án ấn tượng nhất của tôi là xây dựng hệ thống phân tích thị giác máy tính...",
        "filler_words_count": 2,
        "metrics": {
          "confidence_score": 88.0,
          "stress_score": 12.0,
          "content_score": 90.0
        },
        "emotion_timeline": [
          {"second": 1, "emotion": "Normal", "confidence": 0.92},
          {"second": 2, "emotion": "Happy", "confidence": 0.85},
          {"second": 35, "emotion": "Sad", "confidence": 0.68},
          {"second": 50, "emotion": "Normal", "confidence": 0.91}
        ],
        "ai_feedback": {
          "content_critique": "Câu trả lời nêu rõ ràng kinh nghiệm thực tế, áp dụng cấu trúc STAR tốt.",
          "delivery_critique": "Nụ cười tự nhiên ở phần mở đầu tạo thiện cảm tốt. Giây thứ 35 có nét mặt hơi nhăn nhó khi nhắc đến bug kỹ thuật, cần giữ sự tự tin.",
          "suggested_answer": "Nên lượng hóa rõ hơn kết quả dự án (ví dụ: giúp giảm 30% độ trễ hệ thống) để tăng sức thuyết phục."
        }
      }
    ]
  }
  ```

---

## 🛠️ PHẦN 3: ĐẶC TẢ YÊU CẦU CHỨC NĂNG & DỮ LIỆU TINH GỌN

### 3.1. Thiết kế Cơ sở dữ liệu Tinh gọn (Database Schema)
Sử dụng SQLite (hoặc PostgreSQL) gồm **3 bảng quan hệ tinh gọn**, hoàn toàn không lưu trữ file nhị phân:

```sql
-- 1. Bảng Người dùng
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Phiên phỏng vấn
CREATE TABLE interview_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    role_name VARCHAR(100) NOT NULL,
    overall_score FLOAT DEFAULT 0.0,
    confidence_avg FLOAT DEFAULT 0.0,
    stress_avg FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS', -- IN_PROGRESS, COMPLETED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Bảng Chi tiết từng câu hỏi & Đánh giá đa phương thức
CREATE TABLE session_details (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES interview_sessions(id),
    question_text TEXT NOT NULL,
    order_index INT NOT NULL,
    transcript TEXT,                           -- Văn bản bóc băng từ Whisper
    filler_words_count INT DEFAULT 0,          -- Số từ đệm ngập ngừng ("ừm", "à")
    confidence_score FLOAT,                    -- Điểm tự tin từ FER (0.0 - 100.0)
    stress_score FLOAT,                        -- Điểm căng thẳng từ FER (0.0 - 100.0)
    emotion_timeline JSON,                     -- Chuỗi cảm xúc: [{"second": 1, "emotion": "Normal"}, ...]
    ai_feedback JSON,                          -- JSON từ Gemini: {content_score, delivery_critique, suggested_answer}
    status VARCHAR(20) DEFAULT 'PROCESSING'    -- PROCESSING, COMPLETED, FAILED
);
```

### 3.2. Cơ chế Xem Lại Video Client-Side (Blob URL Replay)
1. Trong suốt phiên phỏng vấn, khi `MediaRecorder` ghi xong từng câu, Frontend tạo một Blob:
   ```javascript
   const videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
   const blobUrl = URL.createObjectURL(videoBlob);
   sessionBlobs[questionIndex] = blobUrl; // Lưu trong React State/RAM
   ```
2. Tại màn hình Dashboard Báo cáo:
   - Ứng viên xem lại video trực tiếp từ `blobUrl` mà không cần tải từ Server.
   - Khi ứng viên nhấp vào điểm đỏ (Stress) trên biểu đồ `EmotionTimeline` ở giây thứ 35, hàm điều khiển video được kích hoạt:
   ```javascript
   videoRef.current.currentTime = clickedSecond; // Nhảy ngay đến giây thứ 35
   ```

---

## 👥 PHẦN 4: PHÂN CHIA CÔNG VIỆC CHI TIẾT (TEAM 5 THÀNH VIÊN - 2 TUẦN SPRINT)

Dự án áp dụng nguyên tắc **Decoupled Architecture & API-Contract First**. Trong Tuần 1, Frontend và Backend chạy hoàn toàn độc lập thông qua Mock Data đã thống nhất tại Mục 2.

```
+-----------------------------------------------------------------------------------------------+
|                       MA TRẬN PHÂN CHIA TRÁCH NHIỆM 5 THÀNH VIÊN                              |
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên        | Module & File phụ trách    | Trọng tâm Tuần 1      | Trọng tâm Tuần 2     |
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên A      | ai_core/interview_analytics| Chuyển đổi codebase cũ| Tối ưu thời gian     |
| (AI Lead)         | backend/services/fer_      | thành hàm xử lý video | inference (< 5s), ghép|
|                   | service.py                 | xuất JSON Confidence  | nối vào pipeline ngầm|
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên B      | backend/services/speech_   | Tích hợp Whisper STT  | Tinh chỉnh Prompt    |
| (AI Speech & LLM) | service.py & llm_service.py| & Gemini API trả về   | Gemini chấm STAR, đo |
|                   |                            | JSON nhận xét chuyên  | độ trễ & xử lý lỗi   |
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên C      | backend/ (main.py, api/,   | Dựng FastAPI, SQLite, | Ghép nối 3 service   |
| (Backend Lead)    | database.py, models.py)    | BackgroundTasks & API | vào BackgroundTask,  |
|                   |                            | tự hủy file tạm /tmp/ | deploy Render/Railway|
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên D      | frontend/pages/SetupPage   | Dựng UI chọn ngành/JD,| Nối API nộp câu cuốn |
| (Frontend Room)   | frontend/pages/Interview   | webcam preview, Media | chiếu, quản lý Blob  |
|                   | Room.jsx                   | Recorder & Blob RAM   | RAM không tràn bộ nhớ|
+-------------------+----------------------------+-----------------------+----------------------+
| Thành viên E      | frontend/pages/Dashboard   | Dựng Dashboard Báo cáo| Nối API kết quả thật,|
| (Frontend Dash)   | frontend/components/       | thẻ điểm & biểu đồ    | đồng bộ Replay video |
|                   | EmotionChart.jsx           | Timeline dùng Mock JSON| & Test End-to-End    |
+-------------------+----------------------------+-----------------------+----------------------+
```

---

### 📅 LỊCH TRÌNH THỰC THI CHI TIẾT 14 NGÀY

#### TUẦN 1: TÁI CẤU TRÚC CODEBASE, PHÁT TRIỂN MODULE ĐỘC LẬP (NGÀY 1 – NGÀY 7)

- **Ngày 1 (Cả nhóm):**
  - Chốt toàn bộ tài liệu [SRS.md](file:///d:/emotion_recognition/docs/SRS.md) và API Contracts.
  - Phân chia nhánh Git: `feat/ai-fer`, `feat/ai-speech-llm`, `feat/backend-api`, `feat/fe-room`, `feat/fe-dashboard`.
  - Thành viên C tạo file Mock JSON kết quả phỏng vấn mẫu để Thành viên D và E bắt đầu code giao diện ngay.

- **Ngày 2 – Ngày 5 (Phát triển độc lập theo chuyên môn):**
  - **Thành viên A (AI FER):**
    - Di chuyển code cũ vào `legacy_crowd/`, đưa trọng số vào `weights/crowd_emotion_resnet18.pt`.
    - Viết `backend/services/fer_service.py`: Nhận video path $\rightarrow$ trích xuất frame $\rightarrow$ bắt mặt chính diện $\rightarrow$ dự đoán 4 nhãn qua ResNet-18 $\rightarrow$ tính `confidence_score`, `stress_score` và mảng `emotion_timeline`. Test độc lập với 3 video mp4.
  - **Thành viên B (AI Speech & LLM):**
    - Viết `backend/services/speech_service.py`: Nhận video path $\rightarrow$ tách audio $\rightarrow$ gọi OpenAI Whisper API lấy transcript kèm timestamps, đếm số lần xuất hiện của "ừm", "à", "uhm".
    - Viết `backend/services/llm_service.py`: Tạo client Google Gemini Flash API, thiết kế Prompt sinh JSON theo schema cấu trúc sẵn.
  - **Thành viên C (Backend):**
    - Khởi tạo thư mục `backend/`, cài đặt FastAPI, SQLAlchemy và Pydantic.
    - Viết các bảng CSDL SQLite trong `backend/models.py`.
    - Viết API `POST /api/sessions/start` và `POST /api/sessions/{session_id}/questions/{order_index}/answer` lưu tạm vào `/tmp/` và kích hoạt `BackgroundTasks` giả lập.
  - **Thành viên D (Frontend Phỏng vấn):**
    - Khởi tạo dự án `frontend/` bằng Vite (`npm create vite@latest`).
    - Làm màn hình `SetupPage.jsx`: Chọn ngành nghề, dán JD, kiểm tra camera/micro.
    - Làm màn hình `InterviewRoom.jsx`: Hiển thị câu hỏi, đếm ngược 120s, xử lý nút "Hoàn thành câu", đóng gói Blob WebM lưu RAM.
  - **Thành viên E (Frontend Dashboard):**
    - Làm `DashboardPage.jsx`: Thẻ điểm tổng thể, thanh đo Tự tin / Căng thẳng.
    - Làm `EmotionChart.jsx`: Vẽ biểu đồ đường Timeline cảm xúc theo giây bằng Recharts/Chart.js.
    - Làm `FeedbackAccordion.jsx`: Hiển thị nhận xét chuyên môn và câu trả lời gợi ý từ Mock JSON.

- **Ngày 6 – Ngày 7 (Checkpoint Tuần 1):**
  - Thành viên A và B ghép 2 dịch vụ AI thành hàm duy nhất `analyze_multimodal_answer(video_path)`.
  - Cả nhóm họp demo nội bộ: Frontend chạy thử luồng phỏng vấn với Mock Data; Backend chạy thử AI trên video mẫu thành công.

---

#### TUẦN 2: GHÉP NỐI TOÀN DIỆN, TRIỂN KHAI & BÁO CÁO (NGÀY 8 – NGÀY 14)

- **Ngày 8 – Ngày 9 (Ghép nối AI vào Backend & Tự hủy file tạm):**
  - **Thành viên A, B và C:** Nhúng hàm phân tích AI vào `pipeline_worker.py` của `BackgroundTasks`.
  - Kiểm tra vòng lặp ngầm: Nhận file WebM $\rightarrow$ Lưu `/tmp/` $\rightarrow$ Chạy FER + Whisper + Gemini $\rightarrow$ Cập nhật CSDL SQLite $\rightarrow$ Gọi lệnh `os.remove()` xóa sạch video tạm.
  - Hoàn thiện API `GET /api/sessions/{session_id}/results`.

- **Ngày 10 – Ngày 11 (Ghép nối Frontend với Backend thật):**
  - **Thành viên D & C:** Nối API nộp câu trả lời thật từ phòng phỏng vấn lên Backend. Kiểm tra thời gian phản hồi chuyển câu hỏi đạt $< 800$ms.
  - **Thành viên E & C:** Nối API kết quả thật vào Dashboard, xóa bỏ Mock Data.
  - **Thành viên D & E:** Kích hoạt tính năng đồng bộ phát lại video từ `Blob URL`: Nhấp vào mốc thời gian trên biểu đồ cảm xúc $\rightarrow$ Video nhảy đến đúng giây đó.

- **Ngày 12 (Triển khai & Kiểm thử Tải):**
  - Deploy Backend & Database SQLite lên Render / Railway.
  - Deploy Frontend React lên Vercel / Netlify.
  - Cả nhóm thực hiện 10 lượt phỏng vấn thử nghiệm thực tế với các ngành nghề khác nhau để kiểm tra độ trễ và sửa lỗi logic phát sinh.

- **Ngày 13 – Ngày 14 (Hoàn thiện Báo cáo Đồ án & Thuyết trình):**
  - Phân chia viết báo cáo đồ án:
    - Thành viên A & B: Chương "Phương pháp Đánh giá Đa phương thức (FER, Whisper, LLM)".
    - Thành viên C: Chương "Kiến trúc Hệ thống Bất đồng bộ In-process và Thiết kế CSDL Tinh gọn".
    - Thành viên D & E: Chương "Thiết kế Giao diện Người dùng và Cơ chế Phát lại Video Client-side Blob URL".
  - Chuẩn bị slide thuyết trình và quay video demo hoạt động thực tế.

---

## 🚀 PHẦN 5: ĐỊNH HƯỚNG PHÁT TRIỂN & MỞ RỘNG (LONG-TERM ROADMAP)

Sau khi nghiệm thu thành công MVP 2 tuần, hệ thống có thể mở rộng thành sản phẩm thương mại thông qua 4 định hướng chiến lược:

1. **Phỏng vấn Tương tác Thời gian Thực Thích ứng (Adaptive Dynamic Interviewer):**
   - Thay vì bộ câu hỏi tĩnh, LLM sẽ lắng nghe câu trả lời câu trước để tự động "hỏi xoáy đáp xoay" sinh ra câu hỏi tiếp theo phù hợp với trình độ thực tế của ứng viên.
2. **Theo dõi Giao tiếp Mắt & Ngôn ngữ Cơ thể Nâng cao (Eye Contact & Posture Tracking):**
   - Tích hợp thêm MediaPipe Face Mesh và Pose Estimation để đo đạc tỷ lệ nhìn thẳng vào camera (Eye Contact Rate) và tư thế ngồi ngay ngắn/ngả nghiêng.
3. **Phân tích Ngữ điệu Giọng nói (Speech Emotion & Acoustic Analysis):**
   - Trích xuất đặc trưng âm thanh (Pitch, Energy, Tone) từ giọng nói để đánh giá thêm chỉ số nhiệt huyết, tự tin qua giọng điệu thay vì chỉ dựa vào nét mặt.
4. **Hệ thống Quản lý Phỏng vấn Doanh nghiệp (Enterprise B2B ATS):**
   - Mở rộng phân hệ cho nhà tuyển dụng xem lại báo cáo ứng viên, lọc ứng viên tiềm năng tự động dựa trên xếp hạng điểm số tổng hợp.