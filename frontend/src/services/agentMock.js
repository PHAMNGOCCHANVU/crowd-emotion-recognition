// Mock AI cố vấn dựa trên lịch sử phỏng vấn. API contract:
// GET  /sessions/history                -> [{ session_id, role_name, level, overall_score, content_score,
//                                            voice_score, expression_score, filler_count, stress_level, feedback, created_at }]
// POST /agents/chat                     -> { reply, suggestions[] }
//      body: { message, history: [{ role: 'user' | 'agent', content }], conversation_id }
//      (backend tự lấy lịch sử phiên của user để phân tích)
// GET    /agents/conversations          -> [{ id, title, created_at, updated_at, messages[] }]
// PUT    /agents/conversations/{id}     -> conversation đã lưu
// DELETE /agents/conversations/{id}

import { SESSION_HISTORY } from './mockData';

export const ADVISOR = {
  welcome: 'Xin chào! Mình đã đọc lịch sử luyện tập của bạn. Hãy hỏi mình về kết quả, điểm cần cải thiện hoặc lộ trình luyện tập tiếp theo.',
  suggestions: ['Tóm tắt kết quả của mình', 'Điểm yếu cần cải thiện?', 'Mình có tiến bộ không?', 'Lập lộ trình luyện tập'],
};

const DIMENSIONS = [
  ['content_score', 'Nội dung'],
  ['voice_score', 'Giọng nói'],
  ['expression_score', 'Biểu cảm'],
];

const avg = (list) => (list.length ? list.reduce((s, n) => s + n, 0) / list.length : 0);

export const analyzeHistory = (sessions = SESSION_HISTORY) => {
  if (!sessions.length) return null;
  const sorted = [...sessions].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  const dims = DIMENSIONS.map(([key, label]) => ({ key, label, value: Math.round(avg(sorted.map((s) => s[key] || 0))) }));
  const ranked = [...dims].sort((a, b) => b.value - a.value);
  const half = Math.max(1, Math.floor(sorted.length / 2));
  const early = avg(sorted.slice(0, half).map((s) => s.overall_score));
  const late = avg(sorted.slice(-half).map((s) => s.overall_score));
  const fillers = sorted.map((s) => s.filler_count || 0);
  return {
    total: sorted.length,
    average: Math.round(avg(sorted.map((s) => s.overall_score))),
    latest: sorted[sorted.length - 1],
    best: ranked[0],
    worst: ranked[ranked.length - 1],
    dims,
    trend: Math.round(late - early),
    fillerAvg: Math.round(avg(fillers)),
    fillerDelta: fillers[fillers.length - 1] - fillers[0],
    highStress: sorted.filter((s) => s.stress_level === 'high').length,
    roles: [...new Set(sorted.map((s) => s.role_name))],
  };
};

const FALLBACK_SUGGESTIONS = ['Tóm tắt kết quả của mình', 'Điểm yếu cần cải thiện?', 'Lập lộ trình luyện tập'];

export const mockAgentChat = ({ message }, sessions = SESSION_HISTORY) => {
  const a = analyzeHistory(sessions);
  if (!a) {
    return {
      reply: 'Bạn chưa có phiên phỏng vấn nào. Hãy hoàn thành một phiên luyện tập để mình có dữ liệu phân tích và tư vấn nhé.',
      suggestions: [],
    };
  }
  const text = message.toLowerCase();

  if (/tiến bộ|xu hướng|so sánh/.test(text)) {
    const verb = a.trend > 0 ? `tăng **${a.trend} điểm**` : a.trend < 0 ? `giảm **${-a.trend} điểm**` : 'gần như không đổi';
    return {
      reply: `Điểm trung bình các phiên gần đây so với các phiên đầu ${verb}.\nSố từ đệm mỗi phiên ${a.fillerDelta <= 0 ? `đã giảm ${-a.fillerDelta}` : `tăng ${a.fillerDelta}`} so với lần đầu.\n${a.trend > 0 ? 'Bạn đang đi đúng hướng, hãy giữ nhịp luyện tập đều đặn.' : 'Hãy tập trung sửa một điểm yếu mỗi tuần để thấy tiến bộ rõ hơn.'}`,
      suggestions: ['Điểm yếu cần cải thiện?', 'Lập lộ trình luyện tập'],
    };
  }
  if (/yếu|cải thiện|khuyên/.test(text)) {
    const tips = [`1. **${a.worst.label}** là mảng thấp nhất (${a.worst.value}/100) – ưu tiên luyện phần này.`];
    if (a.fillerAvg > 10) tips.push(`${tips.length + 1}. Trung bình **${a.fillerAvg} từ đệm**/phiên – hãy dừng 1–2 giây thay vì chêm "ừm, à".`);
    if (a.highStress > 0) tips.push(`${tips.length + 1}. Có **${a.highStress} phiên** mức căng thẳng cao – thử hít thở sâu và luyện với câu tình huống.`);
    tips.push(`${tips.length + 1}. Phản hồi gần nhất: *${a.latest.feedback}*`);
    return { reply: tips.join('\n'), suggestions: ['Mình có tiến bộ không?', 'Lập lộ trình luyện tập'] };
  }
  if (/mạnh|ưu điểm/.test(text)) {
    return {
      reply: `Điểm mạnh nhất của bạn là **${a.best.label}** (${a.best.value}/100). Hãy tận dụng nó để dẫn dắt câu trả lời, đồng thời kéo **${a.worst.label}** lên cùng mặt bằng.`,
      suggestions: ['Điểm yếu cần cải thiện?'],
    };
  }
  if (/từ đệm|ừm/.test(text)) {
    return {
      reply: `Trung bình bạn dùng **${a.fillerAvg} từ đệm**/phiên. Cách giảm: ghi âm và nghe lại, chuẩn bị sẵn câu mở đầu cho từng dạng câu hỏi, và dừng ngắn thay vì chêm từ.`,
      suggestions: ['Lập lộ trình luyện tập'],
    };
  }
  if (/lộ trình|kế hoạch|luyện/.test(text)) {
    return {
      reply: `Lộ trình 2 tuần dựa trên lịch sử của bạn:\n**Tuần 1:** luyện **${a.worst.label}** 30 phút/ngày, mỗi ngày 2 câu hỏi cho vị trí ${a.latest.role_name}.\n**Tuần 2:** làm 3 phiên mô phỏng đầy đủ, mục tiêu điểm trung bình trên **${Math.min(95, a.average + 5)}/100**, từ đệm dưới ${Math.max(5, a.fillerAvg - 4)} lần/phiên.`,
      suggestions: ['Mình có tiến bộ không?'],
    };
  }
  if (/tóm tắt|kết quả|điểm/.test(text)) {
    return {
      reply: `Bạn đã hoàn thành **${a.total} phiên** (${a.roles.join(', ')}).\nĐiểm trung bình: **${a.average}/100**, phiên gần nhất: **${a.latest.overall_score}/100**.\nMạnh nhất: **${a.best.label}** (${a.best.value}); cần cải thiện: **${a.worst.label}** (${a.worst.value}).`,
      suggestions: ['Điểm yếu cần cải thiện?', 'Mình có tiến bộ không?'],
    };
  }
  return {
    reply: 'Mình có thể phân tích lịch sử luyện tập của bạn: tóm tắt kết quả, điểm mạnh/yếu, xu hướng tiến bộ hoặc lập lộ trình. Bạn muốn xem phần nào?',
    suggestions: FALLBACK_SUGGESTIONS,
  };
};

// Lưu hội thoại: fallback localStorage khi backend chưa có endpoint
const STORE_KEY = 'il_agent_conversations';

const readStore = () => {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY)) || [];
  } catch {
    return [];
  }
};

const writeStore = (list) => localStorage.setItem(STORE_KEY, JSON.stringify(list));

export const mockListConversations = () =>
  readStore().sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

export const mockSaveConversation = (conv) => {
  const list = readStore().filter((c) => c.id !== conv.id);
  list.push(conv);
  writeStore(list);
  return conv;
};

export const mockDeleteConversation = (id) => {
  writeStore(readStore().filter((c) => c.id !== id));
  return { ok: true };
};
