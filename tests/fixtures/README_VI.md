# Bộ audio kiểm thử tiếng Việt

Ba file WebM được tạo tại máy bằng Windows SpeechSynthesis, giọng Microsoft An
(vi-VN). Nội dung phỏng vấn là tình huống giả định. Đây là giọng đọc tổng hợp,
không phải bản ghi người thật; không mô phỏng đầy đủ tiếng ồn, giọng vùng miền
hoặc cách ngập ngừng tự nhiên.

| File | Thời lượng | Từ đệm trong bản văn | Mục tiêu |
| --- | --- | --- | --- |
| `answer_vi_01.webm` | 26,515 giây | 0 | Câu trả lời đủ STAR, có kết quả định lượng |
| `answer_vi_02.webm` | 27,880 giây | 8 | Nhiều từ đệm, kết quả thiếu số liệu |
| `answer_vi_03.webm` | 18,575 giây | 0 | Hành động chưa rõ, kết quả chưa được xác minh |

Mỗi audio có một file `.txt` cùng tên để đối chiếu transcript.
`vietnamese_cases.json` lưu thông tin audio và nhận xét mong đợi. Số từ đệm
ở trên được tính trên bản văn nguồn; bản bóc băng có thể bỏ hoặc viết khác
từ đệm, nên cần kiểm tra cả audio, transcript và kết quả Regex. Chưa có
word timestamps được gán nhãn thủ công.

Chạy từ thư mục gốc repo bằng PowerShell:

```powershell
.\.venv\Scripts\python.exe -m scripts.benchmark_speech_llm `
  --media tests/fixtures/answer_vi_01.webm `
  --reference tests/fixtures/answer_vi_01.txt `
  --language vi `
  --output artifacts/benchmark-vi-01.json
```

Đổi `01` thành `02` hoặc `03` để chạy các trường hợp còn lại. Mỗi lần chạy
gọi API thật; cần cấu hình `GROQ_API_KEY` và `GEMINI_API_KEY` trong `.env`.
Giữ lại từng kết quả bằng tên output khác nhau nếu chạy lặp. Nếu STT lỗi,
script có thể dùng bản văn đối chiếu để kiểm tra LLM độc lập; lần đó không
được coi là một lượt bóc băng và đánh giá thành công trọn vẹn.

Đối chiếu độ trễ từng bước và tổng độ trễ trong JSON. Bộ dữ liệu này không
đảm bảo API trả lời dưới 3 giây. Để nghiệm thu trên giọng nói thực tế, bổ sung
bản ghi người thật và bản văn được nghe, kiểm tra thủ công.

Tạo lại audio trên Windows đã cài giọng tiếng Việt:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/make_vietnamese_test_audio.ps1
```

Audio dùng Opus, mono, 48 kHz; WAV trung gian lưu trong thư mục `artifacts/`
được Git bỏ qua.
