# 🎙️ AI Mock Interview Platform — Nền Tảng Luyện Phỏng Vấn Thử Thông Minh Đa Phương Thức
> **Đánh giá toàn diện Năng lực Chuyên môn (Verbal) & Phong thái Tự tin (Non-verbal)**  
> *Dự án phát triển ứng dụng thực tiễn từ Codebase Nhận diện Cảm xúc (Emotion Recognition).*

---

## 📌 1. Giới thiệu Đề tài: "Nhận diện cảm xúc ĐỂ LÀM GÌ?"

Trong tuyển dụng hiện đại, nhà tuyển dụng không chỉ đánh giá câu trả lời của ứng viên qua **Nội dung (Verbal)** mà còn quan sát rất kỹ **Phong thái & Ngôn ngữ cơ thể (Non-verbal)**: sự tự tin, độ điềm tĩnh, mức độ căng thẳng khi gặp câu hỏi hóc búa.

**Hệ thống AI Mock Interview giải quyết trọn vẹn bài toán này bằng cách kết hợp 3 trụ cột AI đa phương thức:**
1. **👁️ Thị giác & Phong thái (FER Engine — Kế thừa từ Codebase):** Sử dụng mô hình mạng nơ-ron **ResNet-18** bóc tách biểu cảm vi mô theo từng giây video câu trả lời, tính toán **Chỉ số Tự tin (Confidence Score)** và **Mức độ Căng thẳng (Stress Score)**.
2. **🎙️ Giọng nói & Ngôn từ (Speech Engine — Whisper API):** Bóc băng câu trả lời thành văn bản (Transcript) kèm mốc thời gian, đếm chính xác số lượng từ đệm ngập ngừng ("ừm", "à", "uhm").
3. **🧠 Chuyên môn & Tư duy (Cognitive Engine — Google Gemini Flash API):** Phân tích nội dung câu trả lời theo phương pháp **STAR (Situation - Task - Action - Result)**, đưa ra nhận xét chuyên sâu và gợi ý câu trả lời mẫu tối ưu.
4. **⚡ Lưu trữ Tinh gọn (Ephemeral Storage & Client Blob Replay):** Server **không lưu trữ vĩnh viễn 1 byte video nào** (file tạm tự hủy ngay sau khi trích xuất AI). Ứng viên phát lại video trực tiếp từ bộ nhớ RAM trình duyệt (`Blob URL`) và có thể **nhấp vào mốc thời gian trên biểu đồ cảm xúc để nhảy ngay đến giây tương ứng trên video**.

---

## 🏗️ 2. Kiến trúc Hệ thống Monorepo (Decoupled Architecture)

Toàn bộ dự án được tổ chức theo cấu trúc **Monorepo phân tầng sạch sẽ**:

```
d:\emotion_recognition\
├── 📂 backend/                      ← BACKEND FASTAPI ENGINE
│   ├── main.py                      ← Khởi tạo app FastAPI, CORS, tự sinh DB
│   ├── database.py                  ← Kết nối SQLite (interview.db) & Session
│   ├── models.py                    ← SQLAlchemy ORM models (Users, Sessions, Details)
│   ├── schemas.py                   ← Pydantic schemas (Request / Response DTO)
│   ├── requirements.txt             ← Thư viện backend (fastapi, uvicorn, openai, google-genai...)
│   ├── 📂 api/                      ← Router endpoints (/sessions, /questions)
│   └── 📂 services/                 ← fer_service.py, speech_service.py, llm_service.py, pipeline_worker.py
│
├── 📂 frontend/                     ← FRONTEND REACT + VITE (SPA)
│   ├── package.json                 ← Dependencies: react, axios, lucide-react
│   ├── vite.config.js               ← Cấu hình Vite & reverse proxy sang backend (:8000)
│   ├── index.html                   ← Root HTML template
│   └── 📂 src/
│       ├── App.jsx                  ← Điều phối luồng ứng dụng
│       ├── main.jsx                 ← Entry point React
│       ├── 📂 pages/                ← SetupPage.jsx, InterviewRoom.jsx, DashboardPage.jsx
│       ├── 📂 components/           ← VideoPreview.jsx, EmotionChart.jsx, ScoreCard.jsx, FeedbackAccordion.jsx
│       └── 📂 services/api.js       ← Axios client gọi REST API Backend
│
├── 📂 ai_core/                      ← KẾ THỪA TRỰC TIẾP TỪ CODEBASE HIỆN TẠI
│   ├── crowd_emotion_model.py       ← Mô hình ResNet-18 nhận diện 4 nhãn (Happy, Normal, Sad, Surprised)
│   ├── face_detector.py             ← Phát hiện khuôn mặt chính diện webcam
│   └── interview_analytics.py       ← Thuật toán tính Confidence, Stress Score & Emotion Timeline
│
├── 📂 weights/                      ← TRỌNG SỐ MÔ HÌNH
│   ├── crowd_emotion_resnet18.pt    ← Trọng số mô hình cảm xúc 4 nhãn
│   └── yolov8n-face.pt              ← Trọng số mô hình detector
│
├── 📂 legacy_crowd/                 ← LƯU TRỮ TOÀN BỘ CODE GIÁM SÁT CCTV CŨ (GIỮ LỊCH SỬ)
│   ├── app.py                       ← Streamlit dashboard cũ
│   ├── video_stream.py              ← Pipeline đọc video cũ
│   ├── alert_engine.py              ← Bộ cảnh báo an ninh cũ
│   ├── test_pipeline.py             ← Script test cũ
│   └── live_emotion_recognition.py  ← Code demo cũ của tác giả
│
└── 📂 docs/                         ← TÀI LIỆU DỰ ÁN
    ├── SRS.md                       ← Bản đặc tả yêu cầu phần mềm hoàn thiện
    └── implement_plan.md            ← Kế hoạch thực thi kỹ thuật & API specs
```

---

## 🚀 3. Hướng dẫn Cài đặt & Khởi chạy (Quick Start)

### 3.1. Cài đặt Môi trường
Dự án sử dụng Python 3.10 – 3.12 và Node.js $\ge 18$:

```powershell
# 1. Kích hoạt môi trường ảo Python
.venv\Scripts\activate

# 2. Cài đặt thư viện Python cho Backend & AI Core
pip install -r backend/requirements.txt
```

---

### 3.2. Khởi chạy Hệ thống MỚI: AI Mock Interview Platform

Để chạy hệ thống hoàn chỉnh, bạn mở **2 cửa sổ Terminal**:

#### Terminal 1: Khởi chạy Backend FastAPI
```powershell
# Từ thư mục gốc d:\emotion_recognition:
python -m uvicorn backend.main:app --reload --port 8000
```
* **Tài liệu API tương tác (Swagger UI):** Mở trình duyệt tại **`http://localhost:8000/docs`**
* Server tự động tạo file cơ sở dữ liệu SQLite tại `backend/interview.db`.

#### Terminal 2: Khởi chạy Frontend React (Vite)
```powershell
# Di chuyển vào thư mục frontend:
cd frontend

# Cài đặt dependencies (chỉ cần chạy 1 lần đầu):
npm install

# Khởi chạy Vite Dev Server:
npm run dev
```
* **Giao diện Người dùng:** Mở trình duyệt tại **`http://localhost:5173`**
* Trải nghiệm luồng hoàn chỉnh:
  1. **Thiết lập:** Chọn vị trí tuyển dụng (Software Engineer, Data Analyst, Sales, HR...) hoặc dán JD, kiểm tra camera/micro.
  2. **Phòng phỏng vấn:** Trả lời lần lượt 3 câu hỏi với đồng hồ đếm ngược, MediaRecorder tự động ghi hình WebM.
  3. **Báo cáo Đa phương thức:** Xem thẻ điểm tổng hợp, nghe lại bóc băng, xem biểu đồ Timeline cảm xúc từng giây và nhấp vào mốc để nhảy video phát lại.

---

### 3.3. Cấu hình & Ánh xạ SQLAlchemy sang PostgreSQL (Production / Cloud Database)

Mặc định hệ thống sử dụng SQLite cục bộ (`backend/interview.db`) để chạy thử nghiệm nhanh không cần cài đặt. Khi triển khai Production hoặc triển khai Cloud (Render, Railway, Supabase, Neon), bạn thực hiện ánh xạ các model SQLAlchemy sang **PostgreSQL** theo các bước sau:

#### Bước 1: Cài đặt Driver PostgreSQL
```powershell
pip install psycopg2-binary
```

#### Bước 2: Thiết lập Biến môi trường kết nối (`DATABASE_URL`)
Chuỗi kết nối chuẩn: `postgresql://<username>:<password>@<host>:<port>/<database_name>`

* **Trên Windows PowerShell:**
  ```powershell
  $env:DATABASE_URL = "postgresql://postgres:password123@localhost:5432/interview_db"
  ```
* **Trên Linux / macOS / Bash:**
  ```bash
  export DATABASE_URL="postgresql://postgres:password123@localhost:5432/interview_db"
  ```
* **Hoặc khai báo trong file `.env`:**
  ```env
  DATABASE_URL=postgresql://postgres:password123@localhost:5432/interview_db
  ```

#### Bước 3: Lệnh Thực hiện Ánh xạ Schema sang PostgreSQL
Bạn có thể chọn một trong các cách sau:

* **Cách 1 — Chạy lệnh Python ánh xạ trực tiếp (Khuyên dùng):**
  ```powershell
  python -c "from backend.database import engine, Base; from backend.models import *; Base.metadata.create_all(bind=engine); print('✅ Đã ánh xạ thành công các bảng sang PostgreSQL!')"
  ```

* **Cách 2 — Khởi động Server (Tự động ánh xạ khi Startup):**
  ```powershell
  python -m uvicorn backend.main:app --reload --port 8000
  ```
  *(Khi khởi động, `Base.metadata.create_all(bind=engine)` trong `backend/main.py` sẽ tự động tạo đủ 3 bảng `users`, `interview_sessions`, `session_details` trên PostgreSQL nếu chưa có).*

* **Cách 3 — Sử dụng Alembic Migration (Quản lý phiên bản CSDL):**
  ```powershell
  # Tạo migration script tự động:
  alembic revision --autogenerate -m "Init postgres schema"

  # Đẩy schema lên PostgreSQL:
  alembic upgrade head
  ```

---

### 3.4. Khởi chạy Hệ thống CŨ: Dashboard Streamlit Giám sát CCTV

Nếu bạn muốn mở lại giao diện giám sát đám đông CCTV cũ hoặc chạy kịch bản kiểm thử đo FPS:

```powershell
# Khởi chạy giao diện Streamlit CCTV:
streamlit run legacy_crowd/app.py

# Chạy kịch bản kiểm thử đo đạc hiệu năng FPS:
python legacy_crowd/test_pipeline.py
```
*(Pipeline CCTV đạt tốc độ xử lý **23.6 FPS** trên CPU).*

---

## 🔌 4. Danh sách REST API Endpoints Chính

| Phương thức | Đường dẫn Endpoint | Chức năng chính |
| :--- | :--- | :--- |
| **`POST`** | `/api/sessions/start` | Khởi tạo phiên phỏng vấn mới, sinh 3 câu hỏi theo ngành nghề hoặc JD. |
| **`POST`** | `/api/sessions/{session_id}/questions/{order_index}/answer` | Nộp file video câu trả lời, lưu tạm `/tmp/`, kích hoạt `BackgroundTasks` và trả ngay mã `202 Accepted` trong $< 800$ms. |
| **`GET`** | `/api/sessions/{session_id}/status` | Polling kiểm tra tiến độ xử lý ngầm của các câu hỏi (`PROCESSING` / `COMPLETED`). |
| **`GET`** | `/api/sessions/{session_id}/results` | Lấy toàn bộ kết quả phân tích đa phương thức (thẻ điểm, transcript, emotion timeline, nhận xét Gemini). |
| **`GET`** | `/api/questions/roles` | Lấy danh sách các ngành nghề phỏng vấn mẫu có sẵn. |

---

## 👥 5. Phân công Công việc Nhóm (Sprint 14 Ngày)

Dự án áp dụng nguyên tắc **Decoupled Architecture & API-Contract First** cho nhóm 5 thành viên (A, B, C, D, E):

| Thành viên | Vai trò Kỹ thuật | Trách nhiệm Tuần 1 | Trọng tâm Tuần 2 |
| :--- | :--- | :--- | :--- |
| **Thành viên A** | AI Lead - FER Pipeline | Tái cấu trúc codebase cũ sang `ai_core/`, viết `backend/services/fer_service.py` | Tối ưu hóa FPS, trích xuất Confidence & Stress Score đồng bộ Timeline |
| **Thành viên B** | AI Speech & LLM | Tích hợp Whisper STT (`speech_service.py`) & Gemini API (`llm_service.py`) | Tinh chỉnh Prompt chấm STAR, ghép nối kết quả đa phương thức |
| **Thành viên C** | Backend Lead | Xây dựng FastAPI Core, Database SQLite, In-process `BackgroundTasks` | Ghép nối 3 service vào BackgroundTasks, cơ chế tự hủy file tạm `/tmp/` |
| **Thành viên D** | Frontend Lead - Phòng PV | Xây dựng `SetupPage.jsx`, `InterviewRoom.jsx`, ghi hình `MediaRecorder` | Quản lý bộ nhớ RAM `Blob URL`, nối API nộp câu trả lời cuốn chiếu |
| **Thành viên E** | Frontend Dashboard & QA | Xây dựng `DashboardPage.jsx`, biểu đồ `EmotionChart.jsx` với Mock JSON | Nối API kết quả thật, tính năng nhấp Timeline nhảy video và viết báo cáo |
