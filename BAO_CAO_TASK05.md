# Báo cáo thực hiện Task05 — AI Speech & LLM

**Thành viên thực hiện:** B — Thiên Trường  
**Ngày cập nhật:** 11/10/2026, giờ Việt Nam (UTC+7)  
**Nhánh triển khai trên máy:** `feat/ai-speech-llm`, tạo từ `AI-01`  
**Nguồn yêu cầu:** [Task05 trên Trello](https://trello.com/c/kRVKqM7d/7-task05-ai-speech-llm-thi%C3%AAn-tr%C6%B0%E1%BB%9Dng)

## 1. Kết quả chung

Đã triển khai các chức năng chính của Task05: tách âm thanh và bóc băng có word timestamps, đếm từ đệm, đánh giá bằng Gemini, tiếp nhận dữ liệu cảm xúc, sinh nhận xét và câu trả lời mẫu, fallback khi API gặp sự cố. Các service đã được nối vào pipeline xử lý câu trả lời của backend.

Đã thực hiện kiểm thử giả lập, kiểm thử LLM độc lập bằng bản chép chuẩn và kiểm thử luồng Speech → LLM bằng API thật. Chiến dịch mới nhất hoàn thành **30/30 lượt với Groq và Gemini thật, không có lỗi API**, nhưng chỉ **12/30 lượt (40%)** có tổng thời gian dưới 3 giây.

**Trạng thái Task05: đã hoàn thành phần triển khai chức năng; chưa đạt đầy đủ tiêu chí nghiệm thu về độ trễ và chất lượng đầu ra.** Việc gọi API thành công và trả JSON hợp lệ không đồng nghĩa mọi transcript, timestamps hoặc nhận xét đều chính xác.

## 2. Đối chiếu từng yêu cầu của Task05

| Yêu cầu | Những gì đã thực hiện | Trạng thái và phần còn thiếu |
|---|---|---|
| Whisper STT: tách audio WebM, lấy transcript và word timestamps | Dùng FFmpeg chuyển audio sang WAV mono 16 kHz, PCM 16-bit; gửi lên Groq với model `whisper-large-v3-turbo`, `verbose_json` và timestamps từng từ; kiểm tra cấu trúc kết quả | **Đã triển khai và chạy API thật.** Transcript còn sai một số thuật ngữ; chưa nghe đối chiếu độ chính xác từng timestamp |
| Đếm từ đệm bằng Regex | Nhận diện `ừm`, `à`, `ờ`, `uhm`, `kiểu như`, `thì là`; chuẩn hóa Unicode NFC, không phân biệt hoa/thường, kiểm tra ranh giới từ và khoảng trắng trong cụm; trả tổng và số lượng từng loại | **Đã triển khai.** Đếm trên transcript nhận được; nếu STT bỏ hoặc viết sai từ đệm thì kết quả so với audio vẫn có thể thiếu |
| LLM Evaluator: Gemini Flash và system prompt chuyên gia phỏng vấn | Tích hợp Google Gen AI SDK; system prompt hướng dẫn đánh giá phỏng vấn; yêu cầu JSON theo schema và kiểm tra lại bằng Pydantic | **Đã triển khai và chạy API thật.** Chiến dịch mới nhất dùng `gemini-3.5-flash-lite`; thời gian phản hồi vẫn dao động |
| Đánh giá đa chiều: transcript, cảm xúc và từ đệm → STAR 0–100, nhận xét phong thái, câu trả lời mẫu | Nhận câu hỏi, vai trò, transcript, số từ đệm và dữ liệu FER; hướng dẫn chấm STAR; trả `content_score`, `content_critique`, `delivery_critique`, `suggested_answer` | **Đã triển khai ở mức code.** Chiến dịch 30 lượt không truyền FER thật. Câu trả lời mẫu còn có trường hợp tự thêm hành động/kết quả ngoài dữ kiện |
| Fallback khi API gặp sự cố mạng | Xử lý lỗi kết nối/timeout, HTTP 429 và 5xx khi cho phép fallback; trả kết quả mock có nhãn và metadata; truyền cờ mock từ STT sang LLM | **Đã triển khai.** Chiến dịch nghiệm thu tắt fallback, nên không dùng 30 lượt này làm bằng chứng fallback khi dịch vụ thật bị lỗi |
| Kiểm thử độc lập bóc băng và sinh nhận xét với phản hồi < 3 giây | Có CLI kiểm tra từng service, LLM độc lập bằng bản chuẩn và luồng Speech → LLM; có chiến dịch tự động, báo cáo từng lượt và thống kê | **Đã thực hiện kiểm thử; chưa đạt ngưỡng toàn luồng.** Chỉ 40% trong 30 lượt dưới 3 giây |
| Làm việc trên nhánh riêng và bàn giao | Code trên nhánh `feat/ai-speech-llm` từ `AI-01`; có tài liệu cấu hình, hợp đồng dữ liệu và hướng dẫn kiểm thử | **Đã thực hiện trên máy.** Chưa commit/push phần thay đổi này để bàn giao, theo yêu cầu hiện tại của người thực hiện |

**Thay đổi so với yêu cầu OpenAI Whisper ban đầu:** đã chuyển nhà cung cấp STT sang **Groq Whisper Large V3 Turbo** theo yêu cầu của người thực hiện. Kết quả Groq là kết quả API thật của model Whisper, nhưng không phải bằng chứng nghiệm thu OpenAI Whisper API. Nếu bên nghiệm thu yêu cầu đúng nhà cung cấp OpenAI, cần thống nhất việc thay thế này.

## 3. Các phần đã triển khai

### 3.1. Speech service và word timestamps

File chính: [backend/services/speech_service.py](backend/services/speech_service.py).

- Hàm `transcribe_audio_whisper()` nhận đường dẫn media, giải mã âm thanh, gọi Groq và trả dữ liệu có thể lưu dưới dạng JSON.
- Kiểm tra file đầu vào, định dạng, dung lượng, thời lượng và timeout giải mã; báo lỗi rõ ràng thay vì âm thầm cắt bỏ câu trả lời quá dài.
- Trả transcript, danh sách `{word, start, end}`, thời lượng audio, kết quả từ đệm và metadata nhà cung cấp/model/độ trễ/live hoặc mock.
- Kiểm tra timestamps không âm, `end >= start`, thứ tự bắt đầu và giới hạn thời lượng. Đây là kiểm tra tính hợp lệ của dữ liệu, chưa xác nhận từ được căn đúng với tiếng nói.
- Dọn WAV và thư mục tạm sau khi xử lý, kể cả khi API lỗi; giữ nguyên file media đầu vào cho các bước khác sử dụng.

### 3.2. Đếm từ đệm

Các hàm `count_filler_words()` và `analyze_filler_words()` dùng Regex trong speech service. Ngoài sáu từ/cụm yêu cầu, code giữ các mục có sẵn từ AI-01: `um`, `dạ thì`, `kiểu là`.

Regex tránh đếm ký tự `à` trong `và`, `làm` hoặc `ờ` trong `giờ`. Kết quả gồm tổng số lần xuất hiện và thống kê từng loại. Công cụ chỉ xác định từ/cụm trong văn bản; chưa phân biệt được mọi trường hợp từ xuất hiện với vai trò ngập ngừng hay mang ý nghĩa bình thường.

### 3.3. Gemini evaluator và đánh giá đa chiều

File chính: [backend/services/llm_service.py](backend/services/llm_service.py); hợp đồng dữ liệu tại [backend/services/ai_contracts.py](backend/services/ai_contracts.py).

- Hàm `evaluate_interview_answer_llm()` nhận câu hỏi, vai trò ứng viên, transcript, số từ đệm và dữ liệu cảm xúc.
- Dữ liệu FER hỗ trợ điểm tự tin/căng thẳng, cảm xúc chủ đạo, phân bố cảm xúc và timeline. Thiếu dữ liệu được biểu diễn là thiếu, thay vì tự tạo kết quả FER trong service LLM.
- System prompt hướng dẫn chấm câu hỏi hành vi theo STAR với trọng số Situation 15, Task 15, Action 40, Result 30. Đây là cách phân bổ điểm của phần triển khai; đầu ra hiện có một điểm tổng `content_score`, không có bốn điểm thành phần riêng.
- Nhận xét nội dung tách khỏi nhận xét phong thái. Prompt yêu cầu không suy ra năng lực hoặc độ trung thực từ nét mặt và dùng chỗ trống khi thiếu dữ kiện.
- Yêu cầu Gemini trả JSON đúng schema; kiểm tra điểm 0–100, trường bắt buộc, nội dung không rỗng và phản hồi hoàn chỉnh. Phản hồi sai schema/bị cắt không được ghi nhận thành đánh giá thật hợp lệ.
- Đã điều chỉnh prompt để giới hạn độ dài nhận xét/câu mẫu và dùng thinking mức `LOW`. Chiến dịch gần nhất ghi nhận model `gemini-3.5-flash-lite`.

### 3.4. Fallback và xử lý lỗi

- Fallback chỉ hoạt động khi được bật và gặp lỗi tạm thời thuộc nhóm kết nối, timeout, HTTP 429 hoặc 5xx.
- STT fallback trả transcript và timestamps rỗng, có `metadata.is_mock=true`; LLM fallback trả nội dung có nhãn `[MOCK]`, điểm 0 chỉ là giá trị giữ chỗ.
- Khi STT là mock, LLM nhận `speech_is_mock=True` và không gọi API để đánh giá transcript giả.
- Thiếu key, lỗi xác thực/cấu hình, file lỗi hoặc phản hồi sai schema được báo bằng `ServiceError`, không biến thành kết quả thành công giả.
- Client do service tạo được đóng sau khi dùng. Cả hai service cho phép truyền client từ bên ngoài; việc dùng chung client xuyên nhiều lượt hiện chưa được áp dụng trong chiến dịch này.

### 3.5. Tích hợp vào backend và tài liệu bàn giao

File chính: [backend/services/pipeline_worker.py](backend/services/pipeline_worker.py).

- Pipeline thực hiện FER → Speech → LLM, chuyển dữ liệu cảm xúc, transcript, từ đệm và cờ mock sang evaluator.
- Lưu transcript, từ đệm, điểm, nhận xét, timestamps và metadata nguồn kết quả vào dữ liệu câu trả lời.
- Khi nhận mock, câu được đánh dấu `FAILED`, điểm nội dung trong DB là `null`; kết quả mock không được tính vào điểm tổng của phiên.
- Có xử lý lỗi, cập nhật trạng thái phiên và dọn video tạm sau khi các bước đã sử dụng xong.
- Có hướng dẫn cài dependency, biến môi trường, cách gọi service và chạy CLI. Chưa nghiệm thu toàn bộ ứng dụng gồm frontend, upload, FER thật và DB trong chiến dịch 30 lượt.

## 4. Kiểm thử đã thực hiện và kết quả

### 4.1. Kiểm thử tự động và kiểm thử độc lập

Đã xây dựng các test không cần API key để kiểm tra Regex/Unicode, giải mã media và cleanup, hợp đồng request qua SDK, schema, xử lý lỗi/fallback và truyền dữ liệu giữa các service. Các lần kiểm tra trước trong quá trình triển khai ghi nhận **74 test đạt**; sau đó bộ test riêng cho campaign ghi nhận **13 test đạt**. Đây là kết quả của các lần kiểm tra trước, không phải một lần chạy lại toàn bộ test khi viết báo cáo này.

Đã kiểm thử LLM độc lập bằng cả ba bản chép chuẩn `.txt`, tách khỏi ảnh hưởng sai số STT. Các artifact lưu trong thư mục `artifacts/llm-only-*`. Đã có các lần API trả lỗi 503/504 hoặc cấu hình model sai; những lần đó không được coi là nghiệm thu thành công. Các lần thành công với Flash Lite đã chứng minh LLM gọi được API và trả dữ liệu, nhưng chưa chứng minh mọi phản hồi luôn dưới 3 giây hoặc đạt chất lượng.

### 4.2. Chiến dịch 30 lượt API thật

Script: [scripts/run_speech_llm_campaign.py](scripts/run_speech_llm_campaign.py). Hướng dẫn: [scripts/SPEECH_LLM_CAMPAIGN.md](scripts/SPEECH_LLM_CAMPAIGN.md).

Ba file WebM tiếng Việt được chạy luân phiên, mỗi file 10 lần. Audio là giọng tổng hợp Microsoft An từ bản văn chuẩn, không phải bản thu người thật. Mỗi lượt gọi Groq, dùng transcript thật cùng số từ đệm để gọi Gemini, kiểm tra schema và ghi kết quả riêng; không thay transcript bằng `.txt` và không bật fallback.

Phạm vi đo: **WebM → FFmpeg → Groq STT/timestamps/từ đệm → Gemini → kiểm tra dữ liệu**. Không gồm ghi hình, upload, inference FER, DB, frontend, thời gian nghỉ giữa lượt hoặc ghi báo cáo. Chờ 30 giây sau mỗi lượt; đợt sau được hẹn 2 giờ sau khi đợt trước kết thúc.

| Đợt | Thời gian chạy thực tế ngày 11/10/2026 (UTC+7) | Hoàn thành | Đạt tổng < 3 giây | Trung vị |
|---|---|---:|---:|---:|
| 1 | 09:29:04–09:33:34 | 9/9 | 3/9 | 3,105 giây |
| 2 | 11:33:34–11:38:05 | 9/9 | 3/9 | 3,135 giây |
| 3 | 14:08:41–14:15:16 | 12/12 | 6/12 | 3,568 giây |

Đợt 3 được hẹn lúc 13:38:05 nhưng tiến trình nền đã dừng trước giờ hẹn; trạng thái cuối cập nhật lúc 12:19:12, log không ghi nguyên nhân. Sau khi khởi động lại, runner tiếp tục từ lượt 19 và giữ nguyên kết quả hai đợt đầu. Vì vậy lịch thực tế của đợt 3 bị trễ so với kế hoạch.

| Chỉ tiêu toàn chiến dịch | Kết quả |
|---|---:|
| Số lượt hoàn thành | 30/30 |
| Hoàn thành bằng cả hai API thật | 30/30 |
| Lượt lỗi API | 0 |
| Tổng thời gian dưới 3 giây | 12/30 — 40% |
| Tổng thời gian từ 3 giây trở lên | 18/30 — 60% |
| Trung vị tổng thời gian | 3,120 giây |
| P95 tổng thời gian (nearest-rank) | 8,167 giây |
| Tổng thời gian lớn nhất | 18,023 giây |
| Nghiệm thu mọi lượt dưới 3 giây | **Chưa đạt** |

Lượt chậm nhất là lượt 24: Speech khoảng **16,238 giây**, LLM khoảng **1,785 giây**. Độ trễ không chỉ nằm ở Gemini; cần phân tích riêng từng bước trước khi chọn cách tối ưu. Số liệu hiển thị được làm tròn, nhưng cờ đạt dùng số đo đầy đủ với điều kiện nghiêm ngặt `< 3`.

Bằng chứng tổng hợp:

- [Báo cáo 30 lượt](artifacts/acceptance-20261011-auto/REPORT.md).
- [Thống kê JSON](artifacts/acceptance-20261011-auto/summary.json).
- [Bảng CSV từng lượt](artifacts/acceptance-20261011-auto/results.csv).
- [Kế hoạch và cấu hình được lưu](artifacts/acceptance-20261011-auto/plan.json).
- [Các kết quả chi tiết](artifacts/acceptance-20261011-auto/trials/).

Các artifact là bằng chứng cục bộ, đang thuộc nhóm được Git ignore; cần đính kèm riêng nếu bàn giao báo cáo sang máy khác.

## 5. Những phần chưa đạt hoặc chưa kiểm chứng đầy đủ

1. **Độ trễ toàn luồng dưới 3 giây chưa đạt.** 18/30 lượt vượt hoặc bằng ngưỡng; không dùng thời gian phản hồi mock hay thời gian nhận lỗi để ghi nhận đạt.
2. **Chất lượng STT chưa đạt mức chính xác hoàn toàn.** Đối chiếu trước đã ghi nhận sai các từ kỹ thuật như `backend`, `API`, `log`. Trong chiến dịch 30 lượt, cả 10 lượt của mẫu 02 đều đếm được 7 từ đệm trên transcript, trong khi bản văn chuẩn có 8; sai khác ở STT ảnh hưởng đầu vào Regex.
3. **Câu trả lời mẫu chưa luôn bám sát dữ kiện.** Ví dụ [lượt 003](artifacts/acceptance-20261011-auto/trials/trial-003.json) sinh kết quả “thời gian tải trang đã giảm” và “hệ thống hoạt động ổn định hơn”, trong khi [bản chuẩn mẫu 03](tests/fixtures/answer_vi_03.txt) chưa xác minh hiệu quả. Prompt đã có yêu cầu không bịa nhưng chưa bảo đảm hành vi này trong mọi phản hồi.
4. **Chưa đối chiếu thủ công đầy đủ 30 lượt.** Tất cả kết quả vẫn có `quality_review=pending`; chưa có đánh giá định lượng chất lượng STT, nhãn timestamps hoặc bộ đáp án/chấm điểm chuẩn do người đánh giá xác nhận.
5. **Chưa nghiệm thu trên bản thu người thật và FER thật.** Bộ audio hiện tại là giọng tổng hợp; chiến dịch không cung cấp dữ liệu cảm xúc. Đánh giá đa chiều và fallback đã có code, theo phạm vi đã thống nhất chưa yêu cầu bổ sung kiểm thử live riêng cho hai mục này.
6. **Tự động hóa chưa tự phục hồi sau khi tiến trình bị dừng hoặc máy khởi động lại.** Runner tiếp tục được khi chạy lại, tránh chạy trùng, nhưng chưa có cơ chế tự khởi động cùng Windows hoặc giám sát khởi động lại tiến trình.
7. **Chưa bàn giao các thay đổi bằng commit/push.** Giữ nguyên theo yêu cầu “chưa push lên git”; báo cáo này không thay đổi quyết định đó.

## 6. Công việc còn lại để nghiệm thu đầy đủ

- Tối ưu và đo lại độ trễ từng service; có thể thử tái sử dụng client API, điều chỉnh thinking/độ dài đầu ra trong một chiến dịch mới để so sánh, không cam kết trước sẽ đạt ngưỡng.
- Đối chiếu transcript, từ đệm và timestamps trên bản thu người thật có bản chép và nhãn chuẩn.
- Cải thiện prompt hoặc bổ sung kiểm tra đầu ra để câu trả lời mẫu không tự biến thông tin thiếu thành hành động/thành tích đã xảy ra.
- Hoàn thành đánh giá thủ công chất lượng; nếu nghiệm thu phạm vi toàn ứng dụng, bổ sung FER thật và các bước upload, DB, frontend vào phép đo riêng.
- Thống nhất việc dùng Groq thay cho OpenAI với bên nghiệm thu nếu cần; commit/push và đóng gói bằng chứng khi được yêu cầu bàn giao.

**Kết luận:** Task05 đã có các service, hợp đồng dữ liệu, tích hợp pipeline, fallback và công cụ kiểm thử hoạt động. Đợt kiểm thử mới nhất chứng minh luồng Speech → LLM hoàn thành 30 lượt bằng API thật, nhưng chưa đủ căn cứ đánh dấu hoàn thành toàn bộ Task05 vì tiêu chí độ trễ dưới 3 giây chưa đạt và chất lượng đầu ra còn hạn chế.
