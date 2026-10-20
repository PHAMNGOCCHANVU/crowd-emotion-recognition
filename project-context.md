# NGỮ CẢNH ĐẶC THÙ CỦA DỰ ÁN (PROJECT-SPECIFIC OVERLAY)
> **Hướng dẫn sử dụng:** Đây là file duy nhất bạn cần chỉnh sửa khi bắt đầu một dự án mới.

## 1. Thông tin chung & Kiến trúc
- **Tên dự án:** AI Mock Interview Platform (Nền tảng Luyện Phỏng vấn Thử Thông minh tích hợp AI Đa phương thức)
- **Mô hình kiến trúc:** Decoupled Monorepo (Frontend React SPA, Backend FastAPI REST API, AI Core Đa phương thức)
- **Ngôn ngữ chính & Framework:**
  - **Backend:** Python 3.10 - 3.12 (FastAPI, Uvicorn, Pydantic, SQLAlchemy 2.0, Alembic, ONNX Runtime / PyTorch, OpenCV, Groq Whisper API, Google GenAI SDK / Gemini Flash API, Firebase Admin)
  - **Frontend:** React 18, Vite (SPA), JavaScript, Axios, Lucide React, Vanilla CSS
  - **Database & Cache:** SQLite (mặc định dev tại `backend/interview.db`), PostgreSQL 16 (hỗ trợ Docker / Production qua `DATABASE_URL`), SQLAlchemy ORM
  - **Môi trường:** development
---

## 2. Phân quyền Thư mục cho từng Tác nhân (File Ownership Boundaries)
Các Agent chỉ có quyền **GHI (Write/Modify)** trong các đường dẫn được cấp phép dưới đây:

| Tác nhân (Role) | Đường dẫn được phép GHI (Allowed Write Paths) | Đường dẫn CẤM GHI (Forbidden Paths) |
| :--- | :--- | :--- |
| **Architect Agent** | `docs/specs/**`, `docs/architecture/**`, `openapi.yaml` | Toàn bộ thư mục mã nguồn và cấu hình |
| **Backend Agent** | `backend/**`, `training/**`, `ai_core/**` | `frontend/**`, `tests/**` |
| **Frontend Agent** | `frontend/**` | `backend/**`, `ai_core/**`, `.github/**` |
| **QA / Tester Agent** | `tests/**` | Toàn bộ code nghiệp vụ (chỉ được đọc) |

---

## 3. Bộ lệnh Tiêu chuẩn (Standard CLI Commands)
Các Agent phải sử dụng đúng các câu lệnh dưới đây để tự kiểm tra kết quả:

- **Kiểm tra Linter / Format:**
  - Backend: `.\backend\.venv\Scripts\ruff check backend` (hoặc `ruff check backend`)
  - Frontend: `cd frontend && npm run build`
- **Chạy Unit / Integration Test:**
  - Backend: `.\backend\.venv\Scripts\python.exe -m pytest backend/tests` (hoặc từ thư mục `backend`: `pytest`)
- **Khởi chạy môi trường Local (Dev):**
  - Backend: `cd backend && .\.venv\Scripts\Activate.ps1 && python -m uvicorn main:app --reload --port 8000`
  - Frontend: `cd frontend && npm run dev`
  - Khởi tạo Database: `python backend/init_db.py`
- **Khởi chạy môi trường Container (Docker Compose):**
  - Khởi chạy: `docker compose up --build`
  - Dừng: `docker compose down`

---

## 4. Quy tắc Nghiệp vụ & Kỹ thuật Đặc thù (Domain Rules)
*(Bổ sung các lưu ý riêng của dự án này để Agent tuân thủ)*
- Tính năng phỏng vấn đã chạy ổn định , không đụng vào phần này.