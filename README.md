# 🎙️ AI Mock Interview Platform — Nền Tảng Luyện Phỏng Vấn Thử Thông Minh Đa Phương Thức

Task05 của thành viên B: [cài đặt, hợp đồng Speech/LLM và kiểm thử](backend/SPEECH_LLM.md).
> **Đánh giá toàn diện Năng lực Chuyên môn (Verbal) & Phong thái Tự tin (Non-verbal)**  
> *Dự án phát triển ứng dụng thực tiễn từ Codebase Nhận diện Cảm xúc (Emotion Recognition).*

---

## 📌 1. Giới thiệu Đề tài: "Nhận diện cảm xúc ĐỂ LÀM GÌ?"

Trong tuyển dụng hiện đại, nhà tuyển dụng không chỉ đánh giá câu trả lời của ứng viên qua **Nội dung (Verbal)** mà còn quan sát rất kỹ **Phong thái & Ngôn ngữ cơ thể (Non-verbal)**: sự tự tin, độ điềm tĩnh, mức độ căng thẳng khi gặp câu hỏi hóc búa.

**Hệ thống AI Mock Interview giải quyết trọn vẹn bài toán này bằng cách kết hợp 3 trụ cột AI đa phương thức:**
1. **👁️ Thị giác & Phong thái (FER Engine — Kế thừa từ Codebase):** Sử dụng mô hình mạng nơ-ron **ResNet-18** bóc tách biểu cảm vi mô theo từng giây video câu trả lời, tính toán **Chỉ số Tự tin (Confidence Score)** và **Mức độ Căng thẳng (Stress Score)**.
2. **🎙️ Giọng nói & Ngôn từ (Speech Engine — Groq Whisper Large V3 Turbo API):** Bóc băng câu trả lời thành văn bản (Transcript) kèm mốc thời gian, đếm chính xác số lượng từ đệm ngập ngừng ("ừm", "à", "uhm").
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
│   ├── requirements.txt             ← Thư viện backend (fastapi, uvicorn, groq, google-genai...)
│   ├── 📂 ai_core/                  ← Phân tích cảm xúc và chỉ số phỏng vấn
│   ├── 📂 api/                      ← Router endpoints (sessions, questions, chatbot)
│   ├── 📂 services/                 ← FER, Speech, LLM, pipeline và storage
│   └── 📂 tests/                    ← Kiểm thử service, pipeline và speech/LLM
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
├── 📂 docker-compose.yml             ← PostgreSQL + Backend + Frontend
```

---

## 🚀 3. Hướng dẫn Cài đặt & Khởi chạy (Quick Start)

### 3.1. Cài đặt Môi trường
Dự án sử dụng Python 3.10 – 3.12 và Node.js $\ge 18$:

```powershell
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Tạo môi trường ảo Python riêng cho backend
python -m venv .venv

# 3. Kích hoạt môi trường ảo Python (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 4. Cài đặt thư viện Python cho Backend & AI Core
pip install -r requirements.txt
```

Môi trường Python nằm tại `backend/.venv`, không nằm ở thư mục gốc của dự án.

---

### 3.2. Khởi chạy Hệ thống MỚI: AI Mock Interview Platform

Để chạy hệ thống hoàn chỉnh, bạn mở **2 cửa sổ Terminal**:

#### Terminal 1: Khởi chạy Backend FastAPI
```powershell
# Từ thư mục gốc d:\emotion_recognition:
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
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

### 3.3. Chạy toàn bộ hệ thống bằng Docker Compose (Phục vụ deploy lên server)

Docker Compose khởi chạy PostgreSQL 16, backend FastAPI và frontend Nginx:

```powershell
docker compose up --build
```

Sau khi các container khởi động:

* **Giao diện Người dùng:** `http://localhost`
* **Backend API / Swagger:** `http://localhost:8000/docs`
* **PostgreSQL:** `localhost:5432` (database `interview_db`, user `interview_user`)

Dừng hệ thống bằng `Ctrl+C`, hoặc chạy `docker compose down`. Dữ liệu PostgreSQL được giữ trong volume `postgres_data`.

### 3.4. Cấu hình PostgreSQL cho môi trường local hoặc production

Mặc định, khi không có `DATABASE_URL`, hệ thống sử dụng SQLite cục bộ tại `backend/interview.db`. Khi dùng PostgreSQL, đặt biến môi trường `DATABASE_URL` trước khi khởi động backend. Driver PostgreSQL đã có trong `backend/requirements.txt`.

#### Thiết lập biến môi trường kết nối (`DATABASE_URL`)
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

#### Ánh xạ ORM bằng câu lệnh CLI

Sau khi đã cấu hình `DATABASE_URL` (hoặc để hệ thống dùng SQLite mặc định), chạy script khởi tạo từ thư mục gốc dự án:

```powershell
# Nếu terminal đang ở thư mục backend thì quay về thư mục gốc
cd ..

# Môi trường đã kích hoạt là backend/.venv
python backend/init_db.py
```

Script sẽ nạp toàn bộ SQLAlchemy models, tạo các bảng còn thiếu và kiểm tra cột `video_url` trong bảng `session_details`. Có thể chạy lại lệnh này an toàn khi cần đồng bộ schema hiện tại.

Khi backend khởi động, `Base.metadata.create_all(bind=engine)` tự động tạo các bảng còn thiếu. Với môi trường production, nên dùng migration tool thay vì dựa vào việc tự tạo bảng lúc startup.

---

## 🔌 4. Danh sách REST API Endpoints Chính

| Phương thức | Đường dẫn Endpoint | Chức năng chính |
| :--- | :--- | :--- |
| **`POST`** | `/api/sessions/start` | Khởi tạo phiên phỏng vấn mới, sinh 3 câu hỏi theo ngành nghề hoặc JD. |
| **`POST`** | `/api/sessions/{session_id}/questions/{order_index}/answer` | Nộp file video câu trả lời, lưu tạm `/tmp/`, kích hoạt `BackgroundTasks` và trả ngay mã `202 Accepted` trong $< 800$ms. |
| **`GET`** | `/api/sessions/{session_id}/status` | Polling kiểm tra tiến độ xử lý ngầm của các câu hỏi (`PROCESSING` / `COMPLETED`). |
| **`GET`** | `/api/sessions/{session_id}/results` | Lấy toàn bộ kết quả phân tích đa phương thức (thẻ điểm, transcript, emotion timeline, nhận xét Gemini). |
| **`GET`** | `/api/questions/roles` | Lấy danh sách các ngành nghề phỏng vấn mẫu có sẵn. |
| **`POST`** | `/api/sessions/{session_id}/chat` | Gửi tin nhắn cho chatbot tư vấn trong hoặc sau phiên phỏng vấn. |
| **`GET`** | `/api/sessions/{session_id}/chat/history` | Lấy lịch sử hội thoại của một phiên. |
| **`DELETE`** | `/api/sessions/{session_id}/chat/history` | Xóa lịch sử hội thoại của một phiên. |
| **`GET`** | `/health` | Kiểm tra trạng thái hoạt động của backend. |
