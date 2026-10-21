# Sinh câu hỏi phỏng vấn từ JD

Tính năng backend sinh 3 hoặc 4 câu hỏi mới cho tổ hợp vị trí, level và JD. JD là nguồn chủ đạo; level điều chỉnh độ khó. Theo góp ý của lead, phần này chưa nối vào frontend và chưa thay giao diện. Frontend hiện tại vẫn gọi ngân hàng câu hỏi cũ cho đến khi được tích hợp theo luồng dưới đây.

## Cấu hình

Tái sử dụng `GEMINI_API_KEY` hoặc `GOOGLE_API_KEY`. Model sinh câu hỏi có cấu hình riêng, không thay `GEMINI_MODEL`, system prompt hoặc tiêu chí chấm điểm hiện có:

```dotenv
QUESTION_GENERATION_MODEL=gemini-3.5-flash-lite
QUESTION_GENERATION_TIMEOUT_SECONDS=30
```

Nếu không khai báo hai biến này, backend dùng đúng các giá trị mặc định trên. Nạp `backend/.env` trước, nếu file không tồn tại mới dùng `.env` ở gốc repo. Không cần tạo key mới nếu đã có Gemini key hợp lệ.

Model được chọn có [hỗ trợ structured outputs](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite); SDK dùng [JSON schema](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), sau đó Python kiểm tra lại dữ liệu. Model có thể đổi độc lập bằng biến môi trường, tùy quyền truy cập và quota thực tế.

## Luồng nghiệp vụ để frontend tích hợp sau

1. Người dùng nhập vị trí, chọn level và điền JD.
2. Gọi `POST /api/questions/generate` một lần khi muốn tạo bộ câu hỏi. Không gửi JD trên URL hoặc gọi AI theo từng ký tự nhập.
3. Dùng mảng `questions` trả về để thay danh sách “Câu hỏi bạn sẽ gặp”. Giữ `generated_set_id` của kết quả mới nhất.
4. Nếu vị trí, level hoặc JD thay đổi, hủy lựa chọn bộ cũ và yêu cầu sinh lại trước khi bắt đầu.
5. Khi bấm bắt đầu, gọi `POST /api/sessions/start` bằng `generated_set_id`. Backend chép đúng câu đã xem trước vào `session_details`, không gọi AI lần thứ hai.
6. Speech, FER, evaluator, điểm STAR và công thức tổng hợp tiếp tục chạy như cũ, nhận `question_text` mới từ session detail.

Mỗi lượt sinh thành công tạo một snapshot mới trong `generated_question_sets`, chứa vị trí, level, JD, câu hỏi và metadata. Câu hỏi sinh theo JD không được chèn vào ngân hàng `questions` dùng chung, tránh trộn dữ liệu của những JD khác nhau. Cùng một đầu vào có thể sinh các câu tương tự; không cam kết nội dung khác tuyệt đối giữa các lần gọi model.

## API sinh câu hỏi

Mở `/docs`, chọn **POST /api/questions/generate** và nhập:

```json
{
  "role_name": "Backend Developer",
  "level": "mid",
  "jd_text": "Xây dựng REST API bằng Python và FastAPI. Tối ưu truy vấn PostgreSQL. Viết unit test cho API và xử lý lỗi tích hợp.",
  "question_count": 4
}
```

- `role_name`: tên vị trí, 1–100 ký tự.
- `level`: `intern`, `fresher`, `junior`, `mid` hoặc `senior` (nhãn Mid-level trên UI tương ứng `mid`).
- `jd_text`: bắt buộc, 20–20.000 ký tự sau khi bỏ khoảng trắng đầu/cuối. Không có JD thì API trả 422, không giả vờ đã sinh câu hỏi theo JD.
- `question_count`: chỉ nhận 3 hoặc 4; mặc định 4.

Response HTTP 201 có `generated_set_id`, `role_name`, `level`, `total`, `questions`, `metadata`, `created_at`. Mỗi phần tử `questions` có:

```json
{
  "id": "UUID do backend tạo",
  "order_index": 1,
  "category": "Chuyên môn",
  "question_text": "Bạn chọn những trường hợp nào để viết unit test cho API?",
  "jd_evidence": "Viết unit test cho API",
  "time_limit_seconds": 120
}
```

Đây là ví dụ định dạng, không phải response của một request live cụ thể. `jd_evidence` phải trích một đoạn liên tục trong JD và được Python đối chiếu (chuẩn hóa Unicode, chữ hoa/thường và khoảng trắng). Không trả đáp án, điểm số hay thang chấm trong response sinh câu hỏi.

## Bắt đầu phiên với đúng bộ đã xem

```json
{
  "role_name": "Backend Developer",
  "level": "mid",
  "generated_set_id": "DÁN_MÃ_THẬT_TỪ_RESPONSE_SINH_CÂU_HỎI"
}
```

Gửi payload này tới **POST /api/sessions/start**. Không truyền `question_ids` cùng lúc. Các ID câu hỏi trong preview là ID của snapshot, không phải ID trong ngân hàng `questions`; không dùng chúng với trường `question_ids` cũ.

Nếu bỏ `level` và `jd_text`, backend dùng hai giá trị đã lưu trong snapshot. Nếu có truyền, chúng phải khớp snapshot; vị trí cũng phải khớp. Mã không tồn tại trả 404, ngữ cảnh đã thay đổi trả 409, hai nguồn câu hỏi cùng lúc trả 422. Không âm thầm đổi về câu hỏi mặc định trong các trường hợp này.

Luồng cũ dùng `question_ids` hoặc không có `generated_set_id` được giữ tương thích. Chưa tự thay tất cả phiên cũ thành câu hỏi AI.

## Lỗi và kiểm tra chất lượng

- 422: request thiếu JD, level sai hoặc số câu ngoài 3–4.
- 503: thiếu key/cấu hình chưa hợp lệ hoặc dịch vụ gặp lỗi mạng, timeout, HTTP 5xx.
- 429: provider giới hạn lượt gọi.
- 502: model/key bị provider từ chối hoặc response không hợp lệ.

Tính năng này luôn yêu cầu API thật, không lấy câu hỏi mock hoặc ngân hàng cũ khi lỗi, kể cả khi `AI_MODE=mock`/`AI_ALLOW_FALLBACK=true` của phần đánh giá. UI tích hợp sau cần hiển thị lỗi/thử lại và không dùng bộ của JD cũ cho dữ liệu mới.

Kiểm tra đầu ra: đủ đúng số câu, không trùng câu sau chuẩn hóa, JSON đúng schema, có bằng chứng trong JD, tối đa một câu Hành vi và mỗi câu có 120 giây. Prompt yêu cầu tiếng Việt, độ khó theo level, nội dung theo JD và không làm theo chỉ dẫn chèn vào JD. Việc quote đúng JD không tự chứng minh câu hỏi liên quan về ngữ nghĩa; vẫn cần đánh giá thủ công.

Chạy test offline từ gốc repo:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_question_generation.py backend/tests/test_question_generation_api.py backend/tests/test_llm_service.py -q
```

Kiểm tra API thật độc lập, không ghi DB và không sửa giao diện (lưu request JSON theo ví dụ vào file trước):

```powershell
.\backend\.venv\Scripts\python.exe -X utf8 -m backend.scripts.check_question_generation `
  --request artifacts/question-request.json `
  --output artifacts/question-generation-result.json
```

Khởi động lại backend sau khi cập nhật code. `Base.metadata.create_all()` tạo bảng mới `generated_question_sets`; không cần sửa bảng `questions` hoặc dữ liệu phiên cũ. Không gửi API key vào frontend hoặc commit file `.env`.
