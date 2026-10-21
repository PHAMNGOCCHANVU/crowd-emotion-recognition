import React, { useState, useEffect, useRef } from 'react';
import VideoPreview from '../components/VideoPreview';
import { api } from '../services/api';
import { LEVELS } from '../services/mockData';
import { Camera, ArrowRight, ListChecks, Clock3, Sparkles, BookOpen } from 'lucide-react';

export default function SetupPage({ onStartInterview, initialPositionId, initialLevel }) {
  const [positions, setPositions] = useState([]);
  const [positionId, setPositionId] = useState(initialPositionId || '');
  const [level, setLevel] = useState(initialLevel || '');
  const [questionSource, setQuestionSource] = useState('DEFAULT'); // 'DEFAULT' | 'Q-JD'
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
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

  // Fetch câu hỏi dựa trên positionId, level và questionSource
  useEffect(() => {
    if (!positionId || !level) return;
    let cancelled = false;
    setLoadingQuestions(true);
    api.getQuestions({ positionId, level, source: questionSource }).then((data) => {
      if (cancelled) return;
      setQuestions(data?.questions || []);
      setLoadingQuestions(false);
    });
    return () => {
      cancelled = true;
    };
  }, [positionId, level, questionSource]);

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
      const data = await api.startSession(roleName, '', level, questions.map((q) => q.id));
      isStartingRef.current = true;
      if (onStartInterview) {
        onStartInterview(data, stream);
      }
    } catch (err) {
      console.error('Lỗi khởi tạo phiên:', err);
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
    <div className="page-shell setup-page-revamp">
      <div style={{ marginBottom: '28px' }}>
        <div className="eyebrow">InterviewLab · Sẵn sàng phỏng vấn</div>
        <h1 className="page-title">Chuẩn bị cho buổi phỏng vấn</h1>
        <p className="page-subtitle">
          Kiểm tra thiết bị camera/micro, chọn nguồn câu hỏi và xem trước nội dung trước khi bấm bắt đầu.
        </p>
      </div>

      <div className="setup-grid-top">
        {/* Cột trái: Kiểm tra thiết bị */}
        <div className="panel setup-preview-panel">
          <h3 className="panel-title" style={{ marginBottom: 14 }}>
            <Camera size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />
            Kiểm tra Camera & Micro
          </h3>
          {cameraError ? (
            <div className="setup-camera-err">{cameraError}</div>
          ) : (
            <VideoPreview stream={stream} />
          )}
          <div className="setup-preview-hint">
            💡 Hãy ngồi ở nơi đủ ánh sáng, nhìn thẳng vào camera và nói rõ ràng để AI phân tích nét mặt và giọng nói chính xác nhất.
          </div>
        </div>

        {/* Cột phải: Cấu hình phỏng vấn */}
        <div className="panel setup-config-panel">
          {/* 1. Chọn vị trí */}
          <div className="setup-field">
            <label className="setup-label">1. Vị trí Ứng tuyển</label>
            <select
              value={positionId}
              onChange={(e) => handleChangePosition(e.target.value)}
              className="select-custom"
            >
              {positions.map((p) => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          {/* 2. Chọn level */}
          <div className="setup-field">
            <label className="setup-label">2. Cấp độ (Level)</label>
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

          {/* 3. Segmented Pill Tabs chọn Nguồn câu hỏi */}
          <div className="setup-field">
            <label className="setup-label">3. Nguồn câu hỏi phỏng vấn</label>
            <div className="source-segmented-pills">
              <button
                type="button"
                className={`setup-pill ${questionSource === 'DEFAULT' ? 'active' : ''}`}
                onClick={() => setQuestionSource('DEFAULT')}
              >
                <BookOpen size={14} style={{ marginRight: 6 }} /> Mặc định hệ thống
              </button>
              <button
                type="button"
                className={`setup-pill ${questionSource === 'Q-JD' ? 'active' : ''}`}
                onClick={() => setQuestionSource('Q-JD')}
              >
                <Sparkles size={14} style={{ marginRight: 6 }} /> Sinh từ JD (AI)
              </button>
            </div>
          </div>

          {/* Nút Bắt đầu phỏng vấn */}
          <button
            onClick={handleStart}
            disabled={loading || loadingQuestions || questions.length === 0}
            className="primary-button setup-start-btn"
          >
            {loading ? (
              'Đang khởi tạo...'
            ) : (
              <>
                Bắt đầu phỏng vấn ngay <ArrowRight size={16} style={{ marginLeft: 6 }} />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Cột dưới: "Câu hỏi bạn sẽ gặp" với scroll nội bộ và min-height mở rộng */}
      <div className="panel setup-questions-panel">
        <div className="setup-questions-header">
          <div className="setup-q-title">
            <ListChecks size={18} style={{ marginRight: 8, color: '#38bdf8' }} />
            <span>
              Câu hỏi bạn sẽ gặp{' '}
              {selectedPosition && `· ${selectedPosition.title} (${LEVELS.find((l) => l.id === level)?.label || level})`}
            </span>
          </div>
          <span className="setup-q-count">
            {questions.length} câu hỏi · {questions.length * 2} phút tối đa
          </span>
        </div>

        {loadingQuestions ? (
          <div className="setup-empty-q">Đang nạp câu hỏi xem trước...</div>
        ) : questions.length === 0 ? (
          <div className="setup-empty-q">
            {questionSource === 'Q-JD' ? (
              <div style={{ textAlign: 'center', padding: '16px' }}>
                <p style={{ margin: '0 0 12px 0', color: '#94a3b8' }}>
                  Vị trí này chưa có câu hỏi sinh từ JD nào ở cấp độ này.
                </p>
                <a
                  href={`/practice?role=${positionId}&level=${level}&tab=jd`}
                  className="primary-button btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  <Sparkles size={14} /> Đi tới phân hệ sinh câu hỏi từ JD
                </a>
              </div>
            ) : (
              'Chưa có câu hỏi cho vị trí và cấp độ này.'
            )}
          </div>
        ) : (
          <div className="setup-qr-scrollable styled-scrollbar">
            {questions.map((q, idx) => (
              <div className="setup-qr-card" key={q.id || idx}>
                <div className="setup-qr-number">{idx + 1}</div>
                <div className="setup-qr-main">
                  <div className="setup-qr-text">{q.question_text}</div>
                  <div className="setup-qr-meta">
                    <span className="setup-qr-cat">{q.category}</span>
                    {q.source === 'Q-JD' && (
                      <span className="badge-qjd sm">
                        <Sparkles size={10} /> Từ JD
                      </span>
                    )}
                    <span className="setup-qr-time">
                      <Clock3 size={11} style={{ marginRight: 4 }} />
                      {Math.round((q.time_limit_seconds || 120) / 60)} phút trả lời
                    </span>
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
