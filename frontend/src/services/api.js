import axios from 'axios';
import { mockListPositions, mockListQuestions, mockListRecentResults, mockListSessionHistory } from './mockData';
import { mockAgentChat, mockListConversations, mockSaveConversation, mockDeleteConversation } from './agentMock';

// Local dev dùng proxy '/api'; khi deploy đặt VITE_API_BASE_URL=https://<backend>/api
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

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

  // GET /questions/positions?level=fresher
  getPositions: ({ level } = {}) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/questions/positions`, { params: { level } });
        return ensure(res.data, Array.isArray);
      },
      () => mockListPositions(level)
    ),

  // GET /questions?position_id=backend&level=fresher&source=DEFAULT
  getQuestions: ({ positionId, level, source } = {}) =>
    withMock(
      async () => {
        const params = { position_id: positionId };
        if (level) params.level = level;
        if (source) params.source = source;
        const res = await axios.get(`${API_BASE}/questions`, { params });
        return ensure(res.data, (d) => Array.isArray(d?.questions));
      },
      () => mockListQuestions(positionId, level)
    ),

  // POST /questions/generate-from-jd
  generateQuestionsFromJD: async ({ positionId, level, jdText }) => {
    const res = await axios.post(`${API_BASE}/questions/generate-from-jd`, {
      position_id: positionId,
      level,
      jd_text: jdText,
    });
    return res.data;
  },

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

  // ==========================================
  // ADMIN MANAGEMENT APIS
  // ==========================================

  // Dashboard Stats
  adminGetStats: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/admin/dashboard/stats`);
        return ensure(res.data, (d) => typeof d?.total_sessions === 'number');
      },
      () => ({
        total_users: 12,
        total_sessions: 28,
        completion_rate: 85.7,
        average_score: 78.4,
        recent_sessions: [
          { session_id: 's_01', role: 'Backend Developer', candidate_name: 'Nguyễn Văn A', date: '21/10/2026', status: 'Hoàn thành', score: 85.0 },
          { session_id: 's_02', role: 'Frontend Developer', candidate_name: 'Trần Thị B', date: '21/10/2026', status: 'Hoàn thành', score: 76.5 },
          { session_id: 's_03', role: 'Data Analyst', candidate_name: 'Lê Hoàng C', date: '20/10/2026', status: 'Đang làm', score: 0.0 },
        ],
      })
    ),

  // Users Management
  adminGetUsers: (search) =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/admin/users`, { params: search ? { search } : {} });
        return ensure(res.data, Array.isArray);
      },
      () => [
        { id: 'user_123', email: 'candidate@mockinterview.ai', full_name: 'Nguyễn Minh Đức', phone_number: '0901234567', role: 'USER', session_count: 3, average_score: 82.5, created_at: '2026-10-15T08:00:00' },
        { id: 'user_02', email: 'a.nguyen@email.com', full_name: 'Nguyễn Văn A', phone_number: '0912345678', role: 'USER', session_count: 2, average_score: 85.0, created_at: '2026-10-18T09:30:00' },
        { id: 'user_03', email: 'b.tran@email.com', full_name: 'Trần Thị B', phone_number: '0987654321', role: 'USER', session_count: 1, average_score: 76.5, created_at: '2026-10-20T14:15:00' },
      ].filter((u) => !search || u.full_name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()))
    ),

  adminGetUserSessions: async (userId) => {
    try {
      const res = await axios.get(`${API_BASE}/admin/users/${userId}/sessions`);
      return res.data;
    } catch {
      return [
        { session_id: 's_01', role_name: 'Backend Developer', level: 'junior', overall_score: 82.5, confidence_score: 80.0, stress_score: 20.0, status: 'COMPLETED', created_at: '20/10/2026 15:30' },
      ];
    }
  },

  adminDeleteUser: async (userId) => {
    const res = await axios.delete(`${API_BASE}/admin/users/${userId}`);
    return res.data;
  },

  // Industries Management
  adminGetIndustries: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/admin/industries`);
        return ensure(res.data, Array.isArray);
      },
      () => [
        { id: 'ind_tech', name: 'Công nghệ thông tin', code: 'IT', status: 'ACTIVE', position_count: 4 },
        { id: 'ind_finance', name: 'Tài chính - Ngân hàng', code: 'FIN', status: 'ACTIVE', position_count: 2 },
      ]
    ),

  adminCreateIndustry: async (payload) => {
    const res = await axios.post(`${API_BASE}/admin/industries`, payload);
    return res.data;
  },

  adminUpdateIndustry: async (id, payload) => {
    const res = await axios.patch(`${API_BASE}/admin/industries/${id}`, payload);
    return res.data;
  },

  adminDeleteIndustry: async (id) => {
    const res = await axios.delete(`${API_BASE}/admin/industries/${id}`);
    return res.data;
  },

  // Positions Management
  adminGetPositions: () =>
    withMock(
      async () => {
        const res = await axios.get(`${API_BASE}/admin/positions`);
        return ensure(res.data, Array.isArray);
      },
      () => [
        { id: 'backend', name: 'Backend Developer', code: 'backend', industry_name: 'Công nghệ thông tin', skills: ['Python', 'SQL'], duration: '3–6 tháng', icon: 'server', status: 'ACTIVE', question_count: 10 },
        { id: 'frontend', name: 'Frontend Developer', code: 'frontend', industry_name: 'Công nghệ thông tin', skills: ['React', 'CSS'], duration: '3–6 tháng', icon: 'layout', status: 'ACTIVE', question_count: 8 },
      ]
    ),

  adminCreatePosition: async (payload) => {
    const res = await axios.post(`${API_BASE}/admin/positions`, payload);
    return res.data;
  },

  adminUpdatePosition: async (id, payload) => {
    const res = await axios.patch(`${API_BASE}/admin/positions/${id}`, payload);
    return res.data;
  },

  adminDeletePosition: async (id) => {
    const res = await axios.delete(`${API_BASE}/admin/positions/${id}`);
    return res.data;
  },

  // Questions Management
  adminCreateQuestion: async (payload) => {
    const res = await axios.post(`${API_BASE}/admin/questions`, payload);
    return res.data;
  },

  adminUpdateQuestion: async (id, payload) => {
    const res = await axios.patch(`${API_BASE}/admin/questions/${id}`, payload);
    return res.data;
  },

  adminDeleteQuestion: async (id) => {
    const res = await axios.delete(`${API_BASE}/admin/questions/${id}`);
    return res.data;
  },
};

