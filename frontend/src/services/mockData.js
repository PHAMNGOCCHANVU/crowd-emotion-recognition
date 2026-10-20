// Mock data theo API contract (SRS: ngân hàng câu hỏi là Seed Data trong CSDL).
// Khi backend sẵn sàng, chỉ cần backend trả đúng cấu trúc JSON bên dưới.

export const LEVELS = [
  { id: 'intern', label: 'Intern' },
  { id: 'fresher', label: 'Fresher' },
  { id: 'junior', label: 'Junior' },
  { id: 'mid', label: 'Mid-level' },
  { id: 'senior', label: 'Senior' },
];

export const POSITIONS = [
  { id: 'backend', title: 'Backend Developer', field: 'Công nghệ thông tin', skills: ['Python'], duration: '3–6 tháng', icon: 'server', levels: ['intern', 'fresher', 'junior', 'mid', 'senior'] },
  { id: 'frontend', title: 'Frontend Developer', field: 'Công nghệ thông tin', skills: ['React'], duration: '3–6 tháng', icon: 'layout', levels: ['intern', 'fresher', 'junior', 'mid'] },
  { id: 'data-analyst', title: 'Data Analyst', field: 'Phân tích dữ liệu', skills: ['SQL'], duration: '3–6 tháng', icon: 'chart', levels: ['fresher', 'junior', 'mid'] },
  { id: 'business-analyst', title: 'Business Analyst', field: 'Phân tích nghiệp vụ', skills: ['SQL'], duration: '6–12 tháng', icon: 'briefcase', levels: ['junior', 'mid', 'senior'] },
  { id: 'ai-engineer', title: 'AI Engineer', field: 'Trí tuệ nhân tạo', skills: ['Python'], duration: '6–12 tháng', icon: 'brain', levels: ['junior', 'mid', 'senior'] },
  { id: 'system-analyst', title: 'System Analyst', field: 'Phân tích hệ thống', skills: ['UML'], duration: '1–3 năm', icon: 'network', levels: ['mid', 'senior'] },
  { id: 'sales', title: 'Sales / Business Development', field: 'Kinh doanh', skills: ['Đàm phán'], duration: '3–6 tháng', icon: 'trend', levels: ['intern', 'fresher', 'junior', 'mid'] },
  { id: 'marketing', title: 'Marketing', field: 'Tiếp thị', skills: ['Content'], duration: '3–6 tháng', icon: 'megaphone', levels: ['intern', 'fresher', 'junior', 'mid'] },
  { id: 'hr', title: 'Human Resources (HR)', field: 'Nhân sự', skills: ['Tuyển dụng'], duration: '3–6 tháng', icon: 'users', levels: ['intern', 'fresher', 'junior', 'mid'] },
];

const LEVEL_GROUPS = {
  all: ['intern', 'fresher', 'junior', 'mid', 'senior'],
  entry: ['intern', 'fresher'],
  junior: ['junior'],
  mid: ['mid'],
  senior: ['senior'],
};

// [category, question_text]
const BANK = {
  backend: {
    all: [
      ['Hành vi', 'Bạn hãy giới thiệu bản thân và dự án backend ấn tượng nhất bạn từng tham gia?'],
      ['Hành vi', 'Khi gặp lỗi nghiêm trọng sát giờ bàn giao, bạn ứng phó thế nào?'],
    ],
    entry: [
      ['Chuyên môn', 'REST API là gì? Phân biệt các phương thức GET, POST, PUT, DELETE.'],
      ['Chuyên môn', 'Sự khác biệt giữa SQL và NoSQL là gì? Khi nào dùng loại nào?'],
    ],
    junior: [
      ['Chuyên môn', 'Giải thích index trong cơ sở dữ liệu và khi nào index làm chậm hệ thống.'],
      ['Chuyên môn', 'Sự khác biệt giữa xử lý bất đồng bộ (Async) và đa luồng (Multithread) là gì?'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn thiết kế cơ chế caching cho API có lưu lượng đọc lớn như thế nào?'],
      ['Tình huống', 'API chính chậm đột ngột trên production, bạn điều tra theo các bước nào?'],
    ],
    senior: [
      ['Thiết kế', 'Bạn sẽ tách một monolith thành microservices theo tiêu chí và lộ trình nào?'],
      ['Lãnh đạo', 'Bạn review code và định hướng kỹ thuật cho team như thế nào?'],
    ],
  },
  frontend: {
    all: [
      ['Hành vi', 'Hãy kể về một giao diện bạn tự hào nhất và vai trò của bạn trong đó.'],
      ['Hành vi', 'Bạn xử lý thế nào khi designer và bạn bất đồng về cách hiện thực giao diện?'],
    ],
    entry: [
      ['Chuyên môn', 'Phân biệt state và props trong React.'],
      ['Chuyên môn', 'Box model trong CSS là gì? Phân biệt flexbox và grid.'],
    ],
    junior: [
      ['Chuyên môn', 'useEffect hoạt động ra sao và những lỗi thường gặp với dependency array?'],
      ['Chuyên môn', 'Bạn tối ưu hiệu năng render của một danh sách dài như thế nào?'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn chọn giải pháp quản lý state toàn cục dựa trên tiêu chí nào?'],
      ['Tình huống', 'Trang web tải chậm trên di động, bạn phân tích và cải thiện ra sao?'],
    ],
  },
  'data-analyst': {
    all: [
      ['Hành vi', 'Hãy kể về một lần phân tích dữ liệu giúp đưa ra quyết định quan trọng.'],
      ['Hành vi', 'Bạn trình bày kết quả phân tích cho người không có chuyên môn kỹ thuật như thế nào?'],
    ],
    entry: [
      ['Chuyên môn', 'Phân biệt INNER JOIN và LEFT JOIN trong SQL.'],
      ['Chuyên môn', 'Bạn xử lý dữ liệu thiếu và dữ liệu ngoại lai như thế nào?'],
    ],
    junior: [
      ['Chuyên môn', 'Window function là gì? Cho ví dụ ứng dụng thực tế.'],
      ['Chuyên môn', 'Bạn chọn loại biểu đồ nào để thể hiện xu hướng và so sánh theo nhóm?'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn thiết kế A/B test và đánh giá ý nghĩa thống kê như thế nào?'],
      ['Tình huống', 'Số liệu doanh thu giữa hai báo cáo không khớp nhau, bạn xử lý ra sao?'],
    ],
  },
  'business-analyst': {
    all: [
      ['Hành vi', 'Hãy giới thiệu một dự án bạn đã làm cầu nối giữa nghiệp vụ và kỹ thuật.'],
      ['Hành vi', 'Bạn xử lý thế nào khi các bên liên quan có yêu cầu mâu thuẫn nhau?'],
    ],
    junior: [
      ['Chuyên môn', 'Phân biệt functional và non-functional requirements, cho ví dụ.'],
      ['Chuyên môn', 'User story tốt cần có những thành phần nào?'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn ưu tiên backlog bằng phương pháp nào (MoSCoW, RICE,...)?'],
      ['Tình huống', 'Khách hàng liên tục thay đổi yêu cầu giữa sprint, bạn xử lý ra sao?'],
    ],
    senior: [
      ['Chiến lược', 'Bạn xây dựng business case để thuyết phục ban lãnh đạo đầu tư dự án như thế nào?'],
      ['Lãnh đạo', 'Bạn dẫn dắt và đào tạo BA mới trong team như thế nào?'],
    ],
  },
  'ai-engineer': {
    all: [
      ['Hành vi', 'Hãy kể về một mô hình AI bạn từng xây dựng và kết quả đạt được.'],
      ['Hành vi', 'Bạn giải thích kết quả mô hình cho người không chuyên như thế nào?'],
    ],
    junior: [
      ['Chuyên môn', 'Overfitting là gì? Bạn có những cách nào để giảm overfitting?'],
      ['Chuyên môn', 'Giải thích precision, recall và khi nào ưu tiên chỉ số nào.'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn triển khai và giám sát mô hình trên production như thế nào?'],
      ['Tình huống', 'Độ chính xác của mô hình giảm dần sau vài tháng, bạn điều tra ra sao?'],
    ],
    senior: [
      ['Thiết kế', 'Bạn thiết kế pipeline MLOps từ thu thập dữ liệu đến triển khai như thế nào?'],
      ['Chiến lược', 'Bạn cân nhắc thế nào giữa tự huấn luyện mô hình và dùng API LLM có sẵn?'],
    ],
  },
  'system-analyst': {
    all: [
      ['Hành vi', 'Hãy kể về hệ thống phức tạp nhất bạn từng phân tích và thiết kế.'],
      ['Hành vi', 'Bạn phối hợp với đội phát triển và khách hàng như thế nào để tránh hiểu sai yêu cầu?'],
    ],
    mid: [
      ['Chuyên môn', 'Bạn dùng những sơ đồ UML nào để mô tả một hệ thống và vì sao?'],
      ['Chuyên môn', 'Phân biệt use case diagram và sequence diagram.'],
    ],
    senior: [
      ['Thiết kế', 'Bạn đánh giá và lựa chọn kiến trúc cho hệ thống cần tích hợp nhiều dịch vụ cũ như thế nào?'],
      ['Chiến lược', 'Bạn quản lý nợ kỹ thuật và rủi ro khi di chuyển hệ thống cũ ra sao?'],
    ],
  },
  sales: {
    all: [
      ['Hành vi', 'Hãy giới thiệu bản thân và lý do bạn chọn công việc kinh doanh.'],
      ['Hành vi', 'Kể về một lần bạn bị khách hàng từ chối và bạn đã phản ứng thế nào.'],
    ],
    entry: [
      ['Chuyên môn', 'Bạn tìm hiểu nhu cầu khách hàng trước khi giới thiệu sản phẩm như thế nào?'],
      ['Tình huống', 'Khách hàng nói giá sản phẩm quá cao, bạn trả lời ra sao?'],
    ],
    junior: [
      ['Chuyên môn', 'Bạn xây dựng và duy trì pipeline khách hàng tiềm năng như thế nào?'],
      ['Tình huống', 'Bạn làm gì khi sắp không đạt chỉ tiêu doanh số trong tháng?'],
    ],
    mid: [
      ['Chiến lược', 'Bạn xây dựng kế hoạch chinh phục một khách hàng doanh nghiệp lớn như thế nào?'],
      ['Lãnh đạo', 'Bạn hỗ trợ đồng nghiệp mới đạt hiệu suất bán hàng ra sao?'],
    ],
  },
  marketing: {
    all: [
      ['Hành vi', 'Hãy giới thiệu một chiến dịch marketing bạn ấn tượng và lý do.'],
      ['Hành vi', 'Bạn xử lý thế nào khi chiến dịch không đạt kết quả như kỳ vọng?'],
    ],
    entry: [
      ['Chuyên môn', 'Phân biệt các kênh marketing: SEO, SEM và social media.'],
      ['Chuyên môn', 'Bạn xác định chân dung khách hàng mục tiêu (persona) như thế nào?'],
    ],
    junior: [
      ['Chuyên môn', 'Bạn đo lường hiệu quả chiến dịch bằng những chỉ số nào (CTR, CAC, ROAS,...)?'],
      ['Tình huống', 'Ngân sách bị cắt 30%, bạn điều chỉnh chiến dịch ra sao?'],
    ],
    mid: [
      ['Chiến lược', 'Bạn xây dựng chiến lược ra mắt sản phẩm mới trên thị trường cạnh tranh như thế nào?'],
      ['Lãnh đạo', 'Bạn phân bổ ngân sách giữa các kênh và đánh giá hiệu quả ra sao?'],
    ],
  },
  hr: {
    all: [
      ['Hành vi', 'Hãy giới thiệu bản thân và động lực chọn làm việc trong lĩnh vực nhân sự.'],
      ['Hành vi', 'Kể về một tình huống khó trong giao tiếp với nhân viên và cách bạn xử lý.'],
    ],
    entry: [
      ['Chuyên môn', 'Quy trình tuyển dụng cơ bản gồm những bước nào?'],
      ['Tình huống', 'Bạn sàng lọc hồ sơ ứng viên như thế nào khi nhận được hàng trăm CV?'],
    ],
    junior: [
      ['Chuyên môn', 'Bạn đặt câu hỏi phỏng vấn theo hành vi (STAR) như thế nào?'],
      ['Tình huống', 'Nhân viên giỏi nộp đơn nghỉ việc, bạn xử lý ra sao?'],
    ],
    mid: [
      ['Chiến lược', 'Bạn xây dựng chương trình giữ chân nhân tài như thế nào?'],
      ['Chuyên môn', 'Bạn thiết kế quy trình đánh giá hiệu suất công bằng ra sao?'],
    ],
  },
};

export const QUESTION_BANK = Object.entries(BANK).flatMap(([positionId, groups]) => {
  let seq = 0;
  return Object.entries(groups).flatMap(([group, items]) =>
    items.map(([category, question_text]) => ({
      id: `${positionId}-${++seq}`,
      position_id: positionId,
      levels: LEVEL_GROUPS[group],
      category,
      question_text,
      time_limit_seconds: 120,
    }))
  );
});

export const SESSION_HISTORY = [
  { session_id: 'mock_result_1', role_name: 'Backend Developer', level: 'fresher', overall_score: 85, content_score: 90, voice_score: 80, expression_score: 84, filler_count: 9, stress_level: 'low', feedback: 'Nội dung chuyên môn tốt, cần giảm từ đệm ở phần mở đầu.', created_at: '2026-10-17T10:32:00+07:00' },
  { session_id: 'mock_result_2', role_name: 'Data Analyst', level: 'junior', overall_score: 78, content_score: 82, voice_score: 74, expression_score: 76, filler_count: 14, stress_level: 'medium', feedback: 'Câu trả lời thiếu số liệu minh họa, giọng nói hơi nhanh.', created_at: '2026-10-14T16:18:00+07:00' },
  { session_id: 'mock_result_3', role_name: 'Marketing', level: 'intern', overall_score: 82, content_score: 80, voice_score: 85, expression_score: 81, filler_count: 11, stress_level: 'low', feedback: 'Giao tiếp tự tin, nên bổ sung ví dụ thực tế.', created_at: '2026-10-10T09:45:00+07:00' },
  { session_id: 'mock_result_4', role_name: 'Backend Developer', level: 'intern', overall_score: 70, content_score: 72, voice_score: 68, expression_score: 70, filler_count: 21, stress_level: 'high', feedback: 'Căng thẳng ở câu tình huống, nhiều từ đệm.', created_at: '2026-10-05T20:10:00+07:00' },
  { session_id: 'mock_result_5', role_name: 'Frontend Developer', level: 'intern', overall_score: 66, content_score: 70, voice_score: 63, expression_score: 65, filler_count: 24, stress_level: 'high', feedback: 'Cần luyện cấu trúc câu trả lời STAR.', created_at: '2026-10-01T09:00:00+07:00' },
];

export const RECENT_RESULTS = SESSION_HISTORY.slice(0, 3).map(
  ({ session_id, role_name, level, overall_score, created_at }) => ({ session_id, role_name, level, overall_score, created_at })
);

export const mockListPositions = (level) =>
  POSITIONS.filter((p) => !level || p.levels.includes(level));

export const mockListQuestions = (positionId, level) => {
  const questions = QUESTION_BANK.filter(
    (q) => q.position_id === positionId && (!level || q.levels.includes(level))
  );
  return { position_id: positionId, level: level || null, total: questions.length, questions };
};

export const mockListRecentResults = (limit = 3) => RECENT_RESULTS.slice(0, limit);

export const mockListSessionHistory = () => SESSION_HISTORY;
