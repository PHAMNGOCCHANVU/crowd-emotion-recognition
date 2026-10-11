# Quy trình kiểm thử tự động Speech → LLM

Quy trình dùng `scripts/run_speech_llm_campaign.py`, giữ nguyên logic hai service.
Mỗi lượt là một file WebM → FFmpeg → Groq Whisper → timestamps/từ đệm → Gemini → JSON đánh giá.
Không gồm ghi hình, upload, FER, database hoặc frontend.

## Timeline đã chọn

| Đợt | Lượt | Thời điểm |
|---|---:|---|
| 1 | 9 | Chạy ngay |
| 2 | 9 | 2 giờ sau khi đợt 1 kết thúc |
| 3 | 12 | 2 giờ sau khi đợt 2 kết thúc |

Ba file `answer_vi_01.webm`, `answer_vi_02.webm`, `answer_vi_03.webm` luân phiên;
mỗi file được chạy 10 lần, tổng 30 lượt. Nghỉ **30 giây sau khi mỗi lượt kết thúc**;
khoảng nghỉ không tính vào thời gian xử lý. Đợt sau không chạy sớm hơn lịch.

Các file hiện tại là giọng tổng hợp tiếng Việt; chưa thay thế bộ bản thu người thật.

## Tạo kế hoạch

Chạy từ thư mục gốc repo, sau khi cấu hình `.env`:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_speech_llm_campaign plan `
  --output artifacts/acceptance-my-run `
  --start now --counts 9,9,12 --gap-hours 2 --interval-seconds 30 --max-seconds 3
```

Mỗi chiến dịch dùng một thư mục mới; không ghi đè báo cáo cũ. `plan` không gọi API.
Kế hoạch lưu model/cấu hình công khai, hash code, audio và bản chuẩn; không lưu API key.
Nếu code, audio hoặc cấu hình đang nạp thay đổi khi tiếp tục, runner từ chối trộn kết quả;
tạo chiến dịch mới cho phiên bản mới. Không đổi code/model giữa chiến dịch đang chạy.

## Chạy tự động và tiếp tục

```powershell
.\.venv\Scripts\python.exe -X utf8 -u -m scripts.run_speech_llm_campaign run `
  --campaign artifacts/acceptance-my-run --wait
```

`--wait` giữ tiến trình hoạt động, tự chờ 30 giây giữa lượt và 2 giờ giữa đợt.
Máy cần còn bật, không sleep và có mạng vào lúc chạy API. Các lượt luôn tuần tự, không tạo tải đồng thời.
Nếu không có `--wait`, runner chạy lượt đã đến hạn rồi thoát mã 4 khi cần chờ;
đó không phải lỗi API. Dùng lại lệnh `run ... --wait` để tiếp tục.

Có thể chạy nền bằng PowerShell (thay tên thư mục cho đúng kế hoạch đã tạo):

```powershell
$campaignPath = (Resolve-Path -LiteralPath 'artifacts/acceptance-my-run').Path
$pythonPath = (Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path
$runnerArgs = @('-X', 'utf8', '-u', '-m', 'scripts.run_speech_llm_campaign',
                'run', '--campaign', ('"' + $campaignPath + '"'), '--wait')
$runnerProcess = Start-Process -FilePath $pythonPath -ArgumentList $runnerArgs `
  -WorkingDirectory (Get-Location).Path -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $campaignPath 'stdout.log') `
  -RedirectStandardError (Join-Path $campaignPath 'stderr.log') -PassThru
$runnerProcess.Id
```

Chạy nền không cần giữ terminal mở. Nếu tắt/restart máy hoặc tiến trình bị dừng, dùng lại lệnh
`run ... --wait`; runner không tự khởi động cùng Windows. Nếu lịch đã qua, các lượt còn lại chạy khi
runner được mở lại, vẫn nghỉ 30 giây. Lượt bị gián đoạn giữa chừng được giữ là `interrupted`, không
âm thầm chạy lại hoặc xóa khỏi tỷ lệ đạt. File lock ngăn hai runner chạy cùng chiến dịch.

## Kết quả được cập nhật sau từng lượt

- `plan.json`: kế hoạch và phiên bản cấu hình/code/đầu vào.
- `trials/trial-001.json` … `trial-030.json`: thời điểm, thời gian từng service/tổng, transcript,
  timestamps, từ đệm, nhận xét, điểm, lỗi và cờ live/mock. Nếu LLM lỗi, kết quả Speech vẫn được giữ.
- `results.csv`: một dòng mỗi lượt; mở bằng Excel, UTF-8 BOM.
- `summary.json`: tổng hợp toàn chiến dịch, từng đợt, từng audio; số hoàn thành/lỗi/đạt,
  tỷ lệ đạt, trung vị, P95 nearest-rank và thời gian lớn nhất.
- `REPORT.md`: báo cáo dễ đọc, liên kết tới từng lượt.
- `runner.json`: PID, trạng thái chạy/chờ/kết thúc và thời điểm đến hạn.
- `stdout.log` / `stderr.log`: nhật ký nếu chạy nền theo lệnh trên.

Xem tình trạng:

```powershell
Get-Content artifacts/acceptance-my-run/runner.json
Get-Content artifacts/acceptance-my-run/summary.json
```

Tái tổng hợp từ các báo cáo đã lưu, không gọi API:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_speech_llm_campaign report `
  --campaign artifacts/acceptance-my-run
```

## Tiêu chí và cách đọc

- Mode live, luôn tắt fallback; SDK hiện chỉ gọi một lần, không tự retry để che lượt lỗi.
- STT lỗi thì bỏ qua LLM. Không dùng file .txt thay cho transcript để ghi nhận hoàn thành.
- Lượt đạt độ trễ: cả Groq/Gemini thật, không mock, schema hợp lệ, tổng thực tế **< 3 giây**.
- So sánh trên số đo đầy đủ, không làm tròn 3,001 giây thành lượt đạt.
- Mọi lỗi/gián đoạn/mock vẫn nằm trong số lượt và mẫu số tỷ lệ đạt. Thống kê latency chỉ lấy
  lượt hoàn thành bằng API thật; không trộn thời gian nhận lỗi vào thời gian phản hồi thành công.
- Cả 30 lượt phải đạt nếu muốn nghiệm thu tiêu chí mọi phản hồi dưới 3 giây. P95 dưới 3 giây
  riêng lẻ chưa thay thế điều kiện đó. Các đợt chưa chạy luôn hiển thị chưa hoàn thành.
- Đạt thời gian không đồng nghĩa đạt chất lượng. JSON lưu đủ dữ liệu để tester đối chiếu transcript,
  word timestamps, từ đệm và thông tin LLM tự thêm; `quality_review` mặc định là `pending`.
- Các client hiện tạo mới cho từng lượt, giữ cách đo của benchmark cũ. Nếu thử pooling/thinking/prompt
  khác, tạo chiến dịch mới để đối chiếu. Lượt nhanh không được coi là bằng chứng API luôn nhanh.

Mã thoát `run`: 0 = mọi lượt đạt tiêu chí thời gian; 1 = hoàn tất nhưng có lượt không đạt;
2 = lỗi cấu hình/đường dẫn/phiên bản hoặc runner trùng; 4 = còn lượt chờ và không bật `--wait`;
130 = người dùng ngắt. Report vẫn lưu lượt không đạt.

Kiểm chứng runner mà không gọi API bằng tests với đồng hồ/API giả lập:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_speech_llm_campaign.py -q
```

Smoke test bằng mode mock (chỉ kiểm tra orchestration và FFmpeg, không nghiệm thu API):

```powershell
.\.venv\Scripts\python.exe -m scripts.run_speech_llm_campaign plan `
  --output artifacts/campaign-smoke --mode mock --counts 3,3,3 --gap-hours 0 --interval-seconds 0
.\.venv\Scripts\python.exe -m scripts.run_speech_llm_campaign run `
  --campaign artifacts/campaign-smoke --wait
```

Smoke mock thoát mã 1 vì không có lượt API thật, đúng với tiêu chí nghiệm thu.
