# HỆ THỐNG ĐIỀU PHỐI ĐA TÁC NHÂN (MULTI-AGENT ORCHESTRATION)

Tài liệu này là điểm khởi đầu (Entrypoint) cho mọi AI Agent hoạt động trong dự án. Trước khi thực hiện bất kỳ thay đổi nào, mỗi Agent **BẮT BUỘC** phải đọc hiểu vai trò của mình và tuân thủ nghiêm ngặt quy trình bàn giao dưới đây.

## 1. Kiến trúc Nạp Ngữ cảnh (Context Loading)
Khi một Agent được kích hoạt, hãy nạp ngữ cảnh theo thứ tự ưu tiên sau:
1. **Ngữ cảnh Dự án (Bắt buộc cho tất cả):** Đọc `.ai-agents/project-context.md` để nắm rõ Tech Stack, cấu trúc thư mục và các lệnh chạy thực thi (build, lint, test).
2. **Vai trò Cốt lõi (Theo nhiệm vụ được giao):**
   - Nếu lập kế hoạch/thiết kế: Đọc `.ai-agents/global-roles/architect.md`
   - Nếu viết code Backend/Frontend: Đọc `.ai-agents/global-roles/builder-rules.md`
   - Nếu viết Test/Kiểm tra bảo mật: Đọc `.ai-agents/global-roles/qa-tester.md`

---

## 2. Giao thức Bàn giao & Phối hợp (Handoff Protocol)
Để tránh xung đột code (merge conflict) và hiện tượng "ô nhiễm ngữ cảnh", các Agent hoạt động theo luồng khép kín:

1. **Bước 1 - Đặc tả (Architect Agent):** 
   - Nhận yêu cầu từ người dùng -> Phân tích và xuất bản thiết kế vào `/docs/specs/[ten-tinh-nang].md` (bao gồm DB Schema, API Contract, danh sách file cần sửa).
2. **Bước 2 - Thực thi song song (Builder Agents):**
   - **Backend Agent** và **Frontend Agent** đọc file spec tại `/docs/specs/` và làm việc độc lập trong phạm vi thư mục được cấp quyền.
   - Tuyệt đối không sửa đổi API Contract nếu không thông qua Architect Agent.
3. **Bước 3 - Kiểm định độc lập (QA/Security Agent):**
   - Đọc file spec gốc (không phụ thuộc vào cách hiểu của Builder) để viết Unit Test, Integration Test và E2E Test.
   - Nếu phát hiện lỗi logic hoặc bảo mật, tạo báo cáo lỗi để Builder sửa, **QA tuyệt đối không tự ý sửa code nghiệp vụ**.

---

## 3. Quy tắc An toàn Tối thượng (Global Guardrails)
- **Giới hạn vùng sửa đổi (File Ownership):** Chỉ được phép tạo/sửa/xóa file nằm trong phạm vi `Allowed Paths` đã định nghĩa ở `.ai-agents/project-context.md`.
- **Bảo mật thông tin:** Không bao giờ hardcode API Key, mật khẩu, JWT secret hay thông tin nhạy cảm vào mã nguồn. Luôn sử dụng biến môi trường.
- **Tự xác minh trước khi hoàn tất:** Mọi Agent phải tự chạy lệnh kiểm tra cú pháp (Linter) và biên dịch (Compile/Type-check) thành công trước khi báo cáo hoàn thành nhiệm vụ.
- Đọc `.antigravityignore` và `.clineignore` là để biết được những file không cần đọc, không cần sửa để giảm chi phí token.