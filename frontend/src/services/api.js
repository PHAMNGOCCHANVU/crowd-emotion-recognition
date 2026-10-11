import axios from 'axios';

const API_BASE = '/api';

export const api = {
  // 1. Khởi tạo phiên phỏng vấn
  startSession: async (roleName, jdText = '') => {
    const res = await axios.post(`${API_BASE}/sessions/start`, {
      role_name: roleName,
      jd_text: jdText,
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
};
