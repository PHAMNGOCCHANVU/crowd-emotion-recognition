import axios from 'axios';
import { mockListPositions, mockListQuestions, mockListRecentResults, mockListSessionHistory } from './mockData';
import { mockAgentChat, mockListConversations, mockSaveConversation, mockDeleteConversation } from './agentMock';

// Local dev dùng proxy '/api'; khi deploy có thể đặt domain hoặc domain kèm '/api'.
const configuredApiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const API_BASE = !configuredApiBase
  ? '/api'
  : /\/api$/i.test(configuredApiBase)
    ? configuredApiBase
    : `${configuredApiBase}/api`;

// Tự động gắn X-User-Id header từ localStorage nếu có
axios.interceptors.request.use((config) => {
  try {
    const savedUser = localStorage.getItem('interviewlab_user');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      if (user?.id || user?.user_id) {
        config.headers['X-User-Id'] = user.id || user.user_id;
      }
    }
  } catch (e) {
    // ignore
  }
  return config;
});

// Gọi API thật; nếu backend chưa có endpoint hoặc lỗi thì dùng mock cùng cấu trúc JSON.
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
  id: 'user_123',
  user_id: 'user_123',
  full_name: 'Nguyễn Minh Đức',
  name: 'Nguyễn Minh Đức',
  email: 'candidate@mockinterview.ai',
  role: 'USER',
};

export const api = {
  login: async (email, password) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (!email || !password) throw new Error('Vui lòng nhập email và mật khẩu.');
    if (email.includes('admin')) {
      return {
        id: 'admin_123',
        user_id: 'admin_123',
        full_name: 'Quản trị viên Hệ thống',
        name: 'Quản trị viên Hệ thống',
        email,
        role: 'ADMIN',
      };
    }
    return { ...MOCK_USER, email };
  },

  register: async (name, email, password) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    if (!name || !email || password.length < 6) throw new Error('Mật khẩu cần có ít nhất 6 ký tự.');
    return { ...MOCK_USER, full_name: name, name, email };
  },

  // 1. Khởi tạo phiên phỏng vấn
  startSession: async (roleName, jdText = '', level = 'fresher', questionIds = []) => {
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

  // Alias để bảo đảm tương thích ngược
  submitAnswerVideo: async (sessionId, orderIndex, videoBlob) => {
    return api.uploadAnswer(sessionId, orderIndex, videoBlob);
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

  // 5. Lấy danh sách vị trí phỏng vấn (cũ)
  getRoles: async () => {
    const res = await axios.get(`${API_BASE}/questions/roles`);
    return res.data;
  },

  // Dùng cùng nguồn mock với ngân hàng câu hỏi để ID vị trí luôn khớp.
  getPositions: async ({ level } = {}) => mockListPositions(level),

  // Tạm thời lấy ngân hàng câu hỏi từ mock data của frontend.
  getQuestions: async ({ positionId, level }) => mockListQuestions(positionId, level),

  // GET /sessions/history
  getSessionHistory: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/sessions/history`);
        return ensure(res.data, Array.isArray);
      },
      () => mockListSessionHistory()
    ),

  // GET /sessions/recent?limit=3
  getRecentResults: (limit = 3) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/sessions/recent`, { params: { limit } });
        return ensure(res.data, Array.isArray);
      },
      () => mockListRecentResults(limit)
    ),

  // POST /agents/chat
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

  // GET /agents/conversations
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

  // User Profile
  getUserProfile: async () => {
    try {
      const res = await axios.get(`${API_BASE}/user/profile`);
      return res.data;
    } catch {
      return MOCK_USER;
    }
  },

  updateUserProfile: async (payload) => {
    const res = await axios.patch(`${API_BASE}/user/profile`, payload);
    return res.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const res = await axios.post(`${API_BASE}/user/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return res.data;
  },

  // Segments CRUD
  getSegments: async () => {
    try {
      const res = await axios.get(`${API_BASE}/segments`);
      return res.data;
    } catch {
      return [];
    }
  },

  createSegment: async (payload) => {
    const res = await axios.post(`${API_BASE}/segments`, payload);
    return res.data;
  },

  updateSegment: async (id, payload) => {
    const res = await axios.patch(`${API_BASE}/segments/${id}`, payload);
    return res.data;
  },

  deleteSegment: async (id) => {
    const res = await axios.delete(`${API_BASE}/segments/${id}`);
    return res.data;
  },

  // Admin Positions
  createPosition: async (payload) => {
    const res = await axios.post(`${API_BASE}/admin/positions`, payload);
    return res.data;
  },

  deletePosition: async (id) => {
    const res = await axios.delete(`${API_BASE}/admin/positions/${id}`);
    return res.data;
  },
};
