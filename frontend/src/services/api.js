import axios from 'axios';
import { mockListPositions, mockListQuestions, mockListRecentResults, mockListSessionHistory } from './mockData';
import { mockAgentChat, mockListConversations, mockSaveConversation, mockDeleteConversation } from './agentMock';

const API_BASE = '/api';

// Gọi API thật; nếu backend chưa có endpoint thì dùng mock cùng cấu trúc JSON.
const withMock = async (real, mock) => {
  try {
    return await real();
  } catch {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return mock();
  }
};

const ensure = (data, check) => {
  if (!check(data)) throw new Error('Invalid response');
  return data;
};

const MOCK_USER = {
  user_id: 'mock_user_001',
  name: 'Nguyễn Minh Đức',
  email: 'demo@interviewlab.test',
};

export const api = {
  login: async (email, password) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (!email || !password) throw new Error('Vui lòng nhập email và mật khẩu.');
    return { ...MOCK_USER, email };
  },

  register: async (name, email, password) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (!name || !email || password.length < 6) throw new Error('Mật khẩu cần có ít nhất 6 ký tự.');
    return { ...MOCK_USER, name, email };
  },

  // 1. Khởi tạo phiên phỏng vấn
  startSession: async (roleName, jdText = '', level = null, questionIds = []) => {
    const res = await axios.post(`${API_BASE}/sessions/start`, {
      role_name: roleName,
      jd_text: jdText,
      level,
      question_ids: questionIds,
    });
    return res.data;
  },

  // 2. Upload video WebM từng câu trả lời
  uploadAnswer: async (sessionId, orderIndex, videoBlob) => {
    const formData = new FormData();
    formData.append('video_file', videoBlob, `answer_q${orderIndex}.webm`);

    const res = await axios.post(
      `${API_BASE}/sessions/${sessionId}/questions/${orderIndex}/answer`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return res.data;
  },

  // 3. Polling tiến độ xử lý
  getSessionStatus: async (sessionId) => {
    const res = await axios.get(`${API_BASE}/sessions/${sessionId}/status`);
    return res.data;
  },

  // 4. Lấy toàn bộ kết quả phân tích
  getSessionResults: async (sessionId) => {
    const res = await axios.get(`${API_BASE}/sessions/${sessionId}/results`);
    return res.data;
  },

  // 5. Lấy danh sách vị trí phỏng vấn
  getRoles: async () => {
    const res = await axios.get(`${API_BASE}/questions/roles`);
    return res.data;
  },

  // GET /questions/positions?level=fresher
  // -> [{ id, title, field, skills[], duration, icon, levels[] }]
  getPositions: ({ level } = {}) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/questions/positions`, { params: { level } });
        return ensure(res.data, Array.isArray);
      },
      () => mockListPositions(level)
    ),

  // GET /questions?position_id=backend&level=fresher
  // -> { position_id, level, total, questions: [{ id, category, question_text, time_limit_seconds }] }
  getQuestions: ({ positionId, level }) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/questions`, {
          params: { position_id: positionId, level },
        });
        return ensure(res.data, (d) => Array.isArray(d?.questions));
      },
      () => mockListQuestions(positionId, level)
    ),

  // GET /sessions/history -> [{ session_id, role_name, level, overall_score, content_score,
  //   voice_score, expression_score, filler_count, stress_level, feedback, created_at }]
  getSessionHistory: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/sessions/history`);
        return ensure(res.data, Array.isArray);
      },
      () => mockListSessionHistory()
    ),

  // POST /agents/chat -> { reply, suggestions[] } (backend phân tích lịch sử phiên của user)
  chatWithAgent: ({ conversationId, message, history = [] }) =>
    withMock(
      async () => {
        const res = await axios.post(`${API_BASE}/agents/chat`, {
          conversation_id: conversationId,
          message,
          history,
        });
        return ensure(res.data, (d) => typeof d?.reply === 'string');
      },
      () => mockAgentChat({ message })
    ),

  // GET /agents/conversations -> [{ id, title, created_at, updated_at, messages[] }]
  listConversations: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/agents/conversations`);
        return ensure(res.data, Array.isArray);
      },
      () => mockListConversations()
    ),

  // PUT /agents/conversations/{id}
  saveConversation: (conv) =>
    withMock(
      async () => {
        const res = await axios.put(`${API_BASE}/agents/conversations/${conv.id}`, conv);
        return res.data;
      },
      () => mockSaveConversation(conv)
    ),

  // DELETE /agents/conversations/{id}
  deleteConversation: (id) =>
    withMock(
      async () => {
        const res = await axios.delete(`${API_BASE}/agents/conversations/${id}`);
        return res.data;
      },
      () => mockDeleteConversation(id)
    ),

  // GET /sessions/recent?limit=3
  // -> [{ session_id, role_name, level, overall_score, created_at }]
  getRecentResults: (limit = 3) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/sessions/recent`, { params: { limit } });
        return ensure(res.data, Array.isArray);
      },
      () => mockListRecentResults(limit)
    ),
};
