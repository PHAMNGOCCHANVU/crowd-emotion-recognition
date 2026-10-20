import React, { useState, useEffect, useRef } from 'react';
import VideoPreview from '../components/VideoPreview';
import { api } from '../services/api';
import { LEVELS } from '../services/mockData';
import { Camera, ArrowRight, ListChecks, Clock3 } from 'lucide-react';

export default function SetupPage({ onStartInterview, initialPositionId, initialLevel }) {
  const [positions, setPositions] = useState([]);
  const [positionId, setPositionId] = useState(initialPositionId || '');
  const [level, setLevel] = useState(initialLevel || '');
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [jdText, setJdText] = useState('');
  const [stream, setStream] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const isStartingRef = useRef(false);

  const selectedPosition = positions.find((p) => p.id === positionId);
  const availableLevels = LEVELS.filter((l) => selectedPosition?.levels?.includes(l.id));

  useEffect(() => {
    api.getPositions().then((data) => {
      setPositions(data);
      const first = data.find((p) => p.id === initialPositionId) || data[0];
      if (!first) return;
      setPositionId(first.id);
      setLevel(first.levels?.includes(initialLevel) ? initialLevel : first.levels?.[0] || 'fresher');
    });
  }, [initialPositionId, initialLevel]);

  useEffect(() => {
    if (!positionId || !level) return;
    let cancelled = false;
    setLoadingQuestions(true);
    api.getQuestions({ positionId, level }).then((data) => {
      if (cancelled) return;
      setQuestions(data?.questions || []);
      setLoadingQuestions(false);
    });
    return () => { cancelled = true; };
  }, [positionId, level]);

  const handleChangePosition = (id) => {
    const next = positions.find((p) => p.id === id);
    setPositionId(id);
    if (next && !next.levels?.includes(level)) setLevel(next.levels?.[0] || 'fresher');
  };

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
      // Chỉ ngắt camera khi người dùng rời khỏi trang mà KHÔNG bấm bắt đầu phỏng vấn
      if (!isStartingRef.current && stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const handleStart = async () => {
    if (!selectedPosition || questions.length === 0) return;
    setLoading(true);
    const roleName = selectedPosition.title;
    try {
      const data = await api.startSession(roleName, jdText, level, questions.map((q) => q.id));
      isStartingRef.current = true;
      if (onStartInterview) {
        onStartInterview(data, stream);
      }
    } catch (err) {
      console.error('Lỗi khởi tạo phiên:', err);
      // Fallback demo mock nếu backend chưa bật: dùng đúng các câu hỏi đang review
      const mockSession = {
        session_id: 'mock_demo_' + Date.now(),
        role_name: roleName,
        level,
        total_questions: questions.length,
        questions: questions.map((q, idx) => ({
          order_index: idx + 1,
          question_text: q.question_text,
          time_limit_seconds: q.time_limit_seconds || 120,
        })),
      };
      isStartingRef.current = true;
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
              value={positionId}
              onChange={(e) => handleChangePosition(e.target.value)}
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
              {positions.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              2. Chọn Level
            </label>
            <div className="level-chips">
              {availableLevels.map((l) => (
                <button
                  key={l.id}
                  type="button"
                  className={`level-chip ${level === l.id ? 'active' : ''}`}
                  onClick={() => setLevel(l.id)}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              3. Dán Mô tả Công việc (JD) — Không bắt buộc
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
            disabled={loading || loadingQuestions || questions.length === 0}
            style={{
              padding: '16px',
              borderRadius: '10px',
              border: 'none',
              background: loading || questions.length === 0 ? '#9aa8ba' : '#1e5b9e',
              color: '#fff',
              fontSize: '16px',
              fontWeight: 700,
              cursor: loading || questions.length === 0 ? 'not-allowed' : 'pointer',
              marginTop: '10px',
              transition: 'background 0.2s',
            }}
          >
            {loading ? 'Đang khởi tạo...' : <>Bắt đầu phỏng vấn <ArrowRight size={16} style={{ verticalAlign: 'middle', marginLeft: 5 }} /></>}
          </button>
        </div>
      </div>

      {/* Xem trước câu hỏi để ứng viên review */}
      <div className="panel" style={{ padding: '24px', marginTop: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <h3 className="panel-title">
            <ListChecks size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />
            Câu hỏi bạn sẽ gặp {selectedPosition && `· ${selectedPosition.title} · ${LEVELS.find((l) => l.id === level)?.label || ''}`}
          </h3>
          <span className="muted" style={{ fontSize: 13 }}>{questions.length} câu · tối đa 2 phút/câu</span>
        </div>
        {loadingQuestions ? (
          <div className="uh-empty">Đang tải câu hỏi...</div>
        ) : questions.length === 0 ? (
          <div className="uh-empty">Chưa có câu hỏi cho vị trí và level này.</div>
        ) : (
          <div className="qr-list">
            {questions.map((q, idx) => (
              <div className="qr-item" key={q.id}>
                <span className="qr-num">{idx + 1}</span>
                <div>
                  <div className="qr-text">{q.question_text}</div>
                  <div className="qr-meta">
                    <span className="qr-cat">{q.category}</span>
                    <span><Clock3 size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />{Math.round((q.time_limit_seconds || 120) / 60)} phút</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
