import React, { useState, useEffect } from 'react';
import VideoPreview from '../components/VideoPreview';
import { api } from '../services/api';
import { Camera, ArrowRight, ShieldCheck } from 'lucide-react';

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
    <div className="page-shell">
      <div style={{ marginBottom: '36px' }}>
        <div className="eyebrow">InterviewLab · Practice session</div>
        <h1 className="page-title">
          Chuẩn bị cho buổi phỏng vấn
        </h1>
        <p className="page-subtitle">
          Kiểm tra thiết bị và thiết lập phiên luyện tập trước khi bắt đầu.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px', alignItems: 'start' }}>
        {/* Cột trái: Kiểm tra thiết bị */}
        <div className="panel" style={{ padding: '24px' }}>
          <h3 className="panel-title" style={{ marginBottom: 16 }}>
            <Camera size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />Kiểm tra Camera & Micro
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
        <div className="panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
                background: '#f8fafc',
                color: '#1b2b43',
                border: '1px solid #dce3ed',
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
                background: '#f8fafc',
                color: '#1b2b43',
                border: '1px solid #dce3ed',
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
              background: loading ? '#9aa8ba' : '#1e5b9e',
              color: '#fff',
              fontSize: '16px',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '10px',
              transition: 'background 0.2s',
            }}
          >
            {loading ? 'Đang khởi tạo...' : <>Bắt đầu phỏng vấn <ArrowRight size={16} style={{ verticalAlign: 'middle', marginLeft: 5 }} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}
