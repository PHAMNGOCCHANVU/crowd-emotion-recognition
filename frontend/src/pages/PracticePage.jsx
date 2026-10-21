import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Sparkles,
  Search,
  Filter,
  Clock3,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
} from 'lucide-react';
import { api } from '../services/api';
import { LEVELS } from '../services/mockData';

export default function PracticePage({ onStartInterview }) {
  // Query params parsing
  const searchParams = new URLSearchParams(window.location.search);
  const initialRole = searchParams.get('role') || '';
  const initialLevel = searchParams.get('level') || '';
  const initialTab = searchParams.get('tab') === 'jd' ? 'jd' : 'bank';

  const [activeTab, setActiveTab] = useState(initialTab);
  const [positions, setPositions] = useState([]);

  // Tab 1 state: Ngân hàng câu hỏi
  const [bankRole, setBankRole] = useState(initialRole);
  const [bankLevel, setBankLevel] = useState(initialLevel || '');
  const [bankSource, setBankSource] = useState('all'); // 'all' | 'DEFAULT' | 'Q-JD'
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Tab 2 state: AI sinh câu hỏi từ JD
  const [jdRole, setJdRole] = useState(initialRole);
  const [jdLevel, setJdLevel] = useState(initialLevel || 'junior');
  const [jdText, setJdText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [genMessage, setGenMessage] = useState({ type: '', text: '' });

  // Tải danh sách vị trí
  useEffect(() => {
    api.getPositions().then((data) => {
      setPositions(data);
      if (data.length > 0) {
        if (!bankRole) setBankRole(data[0].id);
        if (!jdRole) setJdRole(data[0].id);
      }
    });
  }, []);

  // Fetch câu hỏi Tab 1
  const fetchQuestions = async () => {
    if (!bankRole) return;
    setLoadingQuestions(true);
    try {
      const res = await api.getQuestions({
        positionId: bankRole,
        level: bankLevel || undefined,
        source: bankSource === 'all' ? undefined : bankSource,
      });
      setQuestions(res?.questions || []);
    } catch (err) {
      console.error('Lỗi tải câu hỏi:', err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [bankRole, bankLevel, bankSource]);

  // Xử lý AI sinh câu hỏi từ JD
  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!jdRole || !jdLevel || jdText.trim().length < 20 || isGenerating) return;

    setIsGenerating(true);
    setGenMessage({ type: '', text: '' });

    try {
      const res = await api.generateQuestionsFromJD({
        positionId: jdRole,
        level: jdLevel,
        jdText: jdText.trim(),
      });

      const count = res?.generated_count || res?.questions?.length || 3;
      setGenMessage({
        type: 'success',
        text: `Tuyệt vời! AI đã sinh thành công ${count} câu hỏi bám sát JD và lưu vào ngân hàng câu hỏi.`,
      });

      // Reset form
      setJdText('');

      // Chuyển sang Tab 1 sau 1.2s và set filter tương ứng
      setTimeout(() => {
        setBankRole(jdRole);
        setBankLevel(jdLevel);
        setBankSource('Q-JD');
        setActiveTab('bank');
        setGenMessage({ type: '', text: '' });
      }, 1200);
    } catch (err) {
      console.error('Lỗi sinh câu hỏi:', err);
      setGenMessage({
        type: 'error',
        text: err?.response?.data?.detail || 'Không thể sinh câu hỏi từ JD. Vui lòng thử lại.',
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedBankPos = positions.find((p) => p.id === bankRole);

  return (
    <div className="page-shell practice-container">
      <div style={{ marginBottom: 28 }}>
        <div className="eyebrow">Luyện tập thông minh · Smart Practice</div>
        <h1 className="page-title">Ôn luyện phỏng vấn</h1>
        <p className="page-subtitle">
          Ngân hàng câu hỏi chuẩn hóa và sinh câu hỏi tự động bám sát Mô tả công việc (JD) bằng AI.
        </p>
      </div>

      {/* Tabs cấp 1 */}
      <div className="practice-tabs">
        <button
          className={`practice-tab-btn ${activeTab === 'bank' ? 'active' : ''}`}
          onClick={() => setActiveTab('bank')}
        >
          <BookOpen size={16} /> Ngân hàng câu hỏi
        </button>
        <button
          className={`practice-tab-btn ${activeTab === 'jd' ? 'active' : ''}`}
          onClick={() => setActiveTab('jd')}
        >
          <Sparkles size={16} /> AI sinh câu hỏi theo JD
        </button>
      </div>

      {/* TAB 1: NGÂN HÀNG CÂU HỎI */}
      {activeTab === 'bank' && (
        <div className="practice-bank-view">
          {/* Bộ lọc thanh ngang */}
          <div className="panel practice-filter-bar">
            {/* Vị trí */}
            <div className="filter-item">
              <label><Filter size={13} /> Vị trí ứng tuyển</label>
              <select
                value={bankRole}
                onChange={(e) => setBankRole(e.target.value)}
                className="select-custom"
              >
                {positions.map((p) => (
                  <option key={p.id} value={p.id}>{p.title}</option>
                ))}
              </select>
            </div>

            {/* Level pills */}
            <div className="filter-item flex-grow">
              <label>Cấp độ (Level)</label>
              <div className="practice-level-pills">
                <button
                  className={`pill-btn ${bankLevel === '' ? 'active' : ''}`}
                  onClick={() => setBankLevel('')}
                >
                  Tất cả
                </button>
                {LEVELS.map((l) => (
                  <button
                    key={l.id}
                    className={`pill-btn ${bankLevel === l.id ? 'active' : ''}`}
                    onClick={() => setBankLevel(l.id)}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Source filter */}
            <div className="filter-item">
              <label>Nguồn gốc câu hỏi</label>
              <div className="source-segmented-control">
                <button
                  className={`seg-btn ${bankSource === 'all' ? 'active' : ''}`}
                  onClick={() => setBankSource('all')}
                >
                  Tất cả
                </button>
                <button
                  className={`seg-btn ${bankSource === 'DEFAULT' ? 'active' : ''}`}
                  onClick={() => setBankSource('DEFAULT')}
                >
                  Mặc định
                </button>
                <button
                  className={`seg-btn ${bankSource === 'Q-JD' ? 'active' : ''}`}
                  onClick={() => setBankSource('Q-JD')}
                >
                  <Sparkles size={12} style={{ marginRight: 4 }} /> Sinh từ JD
                </button>
              </div>
            </div>
          </div>

          {/* Header kết quả */}
          <div className="practice-result-meta">
            <span>
              Tìm thấy <strong>{questions.length}</strong> câu hỏi cho vị trí{' '}
              <strong>{selectedBankPos?.title || 'đã chọn'}</strong>
            </span>
            {onStartInterview && selectedBankPos && (
              <button
                className="primary-button btn-sm"
                onClick={() =>
                  onStartInterview({
                    positionId: selectedBankPos.id,
                    level: bankLevel || 'junior',
                  })
                }
              >
                Luyện tập vị trí này <ArrowRight size={14} />
              </button>
            )}
          </div>

          {/* Danh sách cards */}
          {loadingQuestions ? (
            <div className="practice-loading">
              <Loader2 className="spinner" size={24} /> Đang tải danh sách câu hỏi...
            </div>
          ) : questions.length === 0 ? (
            <div className="panel practice-empty-card">
              <BookOpen size={36} className="practice-empty-icon" />
              <h3>Chưa có câu hỏi nào theo bộ lọc này</h3>
              <p>
                {bankSource === 'Q-JD'
                  ? 'Vị trí này chưa có câu hỏi sinh từ JD. Bạn hãy dùng công cụ AI để sinh câu hỏi ngay!'
                  : 'Hãy thử thay đổi cấp độ hoặc chọn nguồn gốc câu hỏi khác.'}
              </p>
              {bankSource === 'Q-JD' && (
                <button
                  className="primary-button"
                  style={{ marginTop: 12 }}
                  onClick={() => {
                    setJdRole(bankRole);
                    setJdLevel(bankLevel || 'junior');
                    setActiveTab('jd');
                  }}
                >
                  <Sparkles size={15} /> Đi tới công cụ AI sinh câu hỏi từ JD
                </button>
              )}
            </div>
          ) : (
            <div className="practice-q-grid">
              {questions.map((q, idx) => {
                const isJD = q.source === 'Q-JD';
                return (
                  <div key={q.id || idx} className={`practice-q-card ${isJD ? 'is-jd' : ''}`}>
                    <div className="practice-q-head">
                      <span className="practice-q-idx">Câu #{idx + 1}</span>
                      <div className="practice-badges">
                        {isJD ? (
                          <span className="badge-qjd">
                            <Sparkles size={11} /> Sinh từ JD
                          </span>
                        ) : (
                          <span className="badge-default">Chuẩn hóa</span>
                        )}
                        <span className="badge-category">{q.category}</span>
                      </div>
                    </div>

                    <div className="practice-q-body">{q.question_text}</div>

                    <div className="practice-q-footer">
                      <span className="practice-q-meta">
                        <Clock3 size={12} /> {Math.round((q.time_limit_seconds || 120) / 60)} phút chuẩn bị & trả lời
                      </span>
                      {q.created_at && (
                        <span className="practice-q-date">
                          Tạo ngày {new Date(q.created_at).toLocaleDateString('vi-VN')}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AI SINH CÂU HỎI THEO JD */}
      {activeTab === 'jd' && (
        <div className="practice-jd-view">
          <div className="panel practice-jd-card">
            <div className="jd-card-header">
              <div className="jd-header-icon"><Sparkles size={22} /></div>
              <div>
                <h2>AI Trích xuất & Sinh câu hỏi phỏng vấn từ JD</h2>
                <p>
                  Dán nội dung tuyển dụng (Job Description). AI sẽ phân tích từ khóa kỹ thuật cốt lõi
                  và sinh 3 câu hỏi phỏng vấn thực tế lưu trực tiếp vào tài khoản của bạn.
                </p>
              </div>
            </div>

            {genMessage.text && (
              <div className={`profile-alert ${genMessage.type}`} style={{ marginBottom: 20 }}>
                {genMessage.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{genMessage.text}</span>
              </div>
            )}

            <form onSubmit={handleGenerate} className="jd-step-form">
              {/* Bước 1 */}
              <div className="jd-step-row">
                <div className="step-num-badge">1</div>
                <div className="step-content">
                  <label>Chọn Vị trí công việc tương ứng</label>
                  <select
                    value={jdRole}
                    onChange={(e) => setJdRole(e.target.value)}
                    disabled={isGenerating}
                    className="select-custom"
                  >
                    {positions.map((p) => (
                      <option key={p.id} value={p.id}>{p.title}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Bước 2 */}
              <div className="jd-step-row">
                <div className="step-num-badge">2</div>
                <div className="step-content">
                  <label>Chọn Cấp độ yêu cầu của JD</label>
                  <div className="practice-level-pills">
                    {LEVELS.map((l) => (
                      <button
                        key={l.id}
                        type="button"
                        disabled={isGenerating}
                        className={`pill-btn ${jdLevel === l.id ? 'active' : ''}`}
                        onClick={() => setJdLevel(l.id)}
                      >
                        {l.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bước 3 */}
              <div className="jd-step-row">
                <div className="step-num-badge">3</div>
                <div className="step-content">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <label style={{ margin: 0 }}>Dán toàn bộ nội dung Mô tả Công việc (JD)</label>
                    <span className={`char-counter ${jdText.trim().length >= 20 ? 'valid' : 'invalid'}`}>
                      {jdText.trim().length} / tối thiểu 20 ký tự
                    </span>
                  </div>
                  <textarea
                    rows={7}
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                    disabled={isGenerating}
                    placeholder="Ví dụ: Tuyển dụng Backend Engineer (FastAPI/Python, PostgreSQL, Redis, Docker, Git). Yêu cầu ứng viên có tư duy hệ thống tốt, hiểu biết về RESTful API và tối ưu hóa truy vấn..."
                    className="jd-textarea"
                  />
                  <small className="form-hint">
                    💡 Mẹo: Dán chi tiết phần "Yêu cầu ứng viên" và "Mô tả công việc" để AI sinh các câu hỏi tình huống và chuyên môn sát thực tế nhất.
                  </small>
                </div>
              </div>

              {/* Action Trigger */}
              <div className="jd-action-row">
                <button
                  type="submit"
                  disabled={!jdRole || !jdLevel || jdText.trim().length < 20 || isGenerating}
                  className="primary-button jd-submit-btn"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="spinner" size={18} /> Đang phân tích JD và sinh câu hỏi...
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} /> AI Sinh câu hỏi từ JD
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
