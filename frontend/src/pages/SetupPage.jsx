import React, { useState, useEffect } from 'react';
import VideoPreview from '../components/VideoPreview';
import { api } from '../services/api';

const ROLES = [
  'Software Engineer',
  'Data Analyst',
  'Sales / Business Development',
  'Marketing',
  'Human Resources (HR)',
];

export default function SetupPage({ onStartInterview }) {
  const [selectedRole, setSelectedRole] = useState(ROLES[0]);
  const [jdText, setJdText] = useState('');
  const [stream, setStream] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState('');

  useEffect(() => {
    // Kích hoạt camera để ứng viên kiểm tra thiết bị
    navigator.mediaDevices
      ?.getUserMedia({ video: true, audio: true })
      .then((s) => {
        setStream(s);
        setCameraError('');
      })
      .catch((err) => {
        console.warn('Lỗi mở camera:', err);
        setCameraError('Không thể mở camera hoặc micro. Vui lòng cấp quyền truy cập trình duyệt.');
      });

    return () => {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
      const data = await api.startSession(selectedRole, jdText);
      if (onStartInterview) {
        onStartInterview(data, stream);
      }
    } catch (err) {
      console.error('Lỗi khởi tạo phiên:', err);
      // Fallback demo mock nếu backend chưa bật
      const mockSession = {
        session_id: 'mock_demo_' + Date.now(),
        role_name: selectedRole,
        total_questions: 3,
        questions: [
          { order_index: 1, question_text: 'Bạn hãy giới thiệu bản thân và dự án ấn tượng nhất bạn từng tham gia?', time_limit_seconds: 120 },
          { order_index: 2, question_text: 'Khi gặp lỗi nghiêm trọng sát giờ bàn giao, bạn ứng phó thế nào?', time_limit_seconds: 120 },
          { order_index: 3, question_text: 'Sự khác biệt giữa xử lý bất đồng bộ (Async) và đa luồng (Multithread) là gì?', time_limit_seconds: 120 },
        ],
      };
      if (onStartInterview) onStartInterview(mockSession, stream);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '40px auto', padding: '0 20px' }}>
      <div style={{ textAlign: 'center', marginBottom: '36px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 800, margin: '0 0 10px', color: '#f8fafc' }}>
          🎯 AI Mock Interview Platform
        </h1>
        <p style={{ fontSize: '16px', color: '#94a3b8', margin: 0 }}>
          Luyện phỏng vấn thử đa phương thức: Đánh giá đồng thời Chuyên môn (Verbal) & Phong thái tự tin (Non-verbal)
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px', alignItems: 'start' }}>
        {/* Cột trái: Kiểm tra thiết bị */}
        <div style={{ background: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155' }}>
          <h3 style={{ margin: '0 0 16px', fontSize: '18px', color: '#f1f5f9' }}>
            📹 Kiểm tra Camera & Micro
          </h3>
          {cameraError ? (
            <div style={{ padding: '20px', background: '#451a1a', borderRadius: '12px', color: '#fca5a5', fontSize: '14px' }}>
              {cameraError}
            </div>
          ) : (
            <VideoPreview stream={stream} />
          )}
          <div style={{ marginTop: '16px', fontSize: '13px', color: '#94a3b8', lineHeight: 1.5 }}>
            💡 Hãy ngồi ở nơi đủ ánh sáng, nhìn thẳng vào camera và nói rõ ràng để AI phân tích nét mặt và giọng nói chính xác nhất.
          </div>
        </div>

        {/* Cột phải: Chọn ngành nghề & JD */}
        <div style={{ background: '#1e293b', padding: '24px', borderRadius: '16px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              1. Chọn Vị trí Ứng tuyển
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #475569',
                fontSize: '14px',
                outline: 'none',
              }}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              2. Dán Mô tả Công việc (JD) — Không bắt buộc
            </label>
            <textarea
              rows={4}
              placeholder="Dán nội dung Job Description (JD) vào đây để AI sinh câu hỏi phỏng vấn sát thực tế..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #475569',
                fontSize: '13px',
                outline: 'none',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <button
            onClick={handleStart}
            disabled={loading}
            style={{
              padding: '16px',
              borderRadius: '10px',
              border: 'none',
              background: loading ? '#475569' : '#3b82f6',
              color: '#fff',
              fontSize: '16px',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '10px',
              transition: 'background 0.2s',
            }}
          >
            {loading ? 'Đang khởi tạo...' : '🚀 Bắt đầu Phỏng vấn Thử'}
          </button>
        </div>
      </div>
    </div>
  );
}
