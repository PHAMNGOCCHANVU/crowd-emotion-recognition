import React, { useEffect, useState } from 'react';
import { History as HistoryIcon, ArrowRight, Award, Clock } from 'lucide-react';
import { api } from '../services/api';

const LEVEL_LABEL = {
  intern: 'Intern',
  fresher: 'Fresher',
  junior: 'Junior',
  mid: 'Mid-level',
  middle: 'Middle',
  senior: 'Senior',
};

const formatDate = (iso) =>
  new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

export default function HistoryPage({ onViewSessionDetail }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getSessionHistory()
      .then((list) => {
        setSessions([...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      })
      .finally(() => setLoading(false));
  }, []);

  const handleRowClick = (sessionId) => {
    if (onViewSessionDetail) {
      onViewSessionDetail(sessionId);
    } else {
      window.location.href = `/results?session_id=${sessionId}`;
    }
  };

  return (
    <div className="page-shell history-revamp-page">
      <div style={{ marginBottom: 28 }}>
        <div className="eyebrow">Hoạt động của bạn · Activity History</div>
        <h1 className="page-title">Lịch sử phỏng vấn</h1>
        <p className="page-subtitle">
          Danh sách toàn bộ các phiên phỏng vấn thử bạn đã thực hiện. Bấm vào từng phiên để xem chi tiết kết quả, phân tích FER và phản hồi của AI.
        </p>
      </div>

      <div className="panel history-container-panel">
        <div className="history-header-bar">
          <div className="history-head-title">
            <HistoryIcon size={18} />
            <span>Tất cả phiên phỏng vấn ({sessions.length})</span>
          </div>
          <span className="history-hint-text">
            💡 Nhấp vào bất kỳ phiên nào để xem lại video và báo cáo chi tiết
          </span>
        </div>

        {loading ? (
          <div className="uh-empty">Đang tải lịch sử phỏng vấn...</div>
        ) : sessions.length === 0 ? (
          <div className="uh-empty">
            Bạn chưa hoàn thành phiên phỏng vấn nào. Hãy bắt đầu buổi luyện tập đầu tiên!
          </div>
        ) : (
          <div className="history-cards-list">
            {sessions.map((s) => (
              <div
                className="history-interactive-row"
                key={s.session_id}
                onClick={() => handleRowClick(s.session_id)}
                role="button"
                tabIndex={0}
              >
                <div className="history-main-info">
                  <div className="history-role-line">
                    <span className="history-role-title">{s.role_name}</span>
                    <span className="history-level-badge">
                      {LEVEL_LABEL[s.level] || s.level}
                    </span>
                  </div>
                  <div className="history-date-line">
                    <Clock size={13} style={{ marginRight: 4 }} />
                    {formatDate(s.created_at)}
                  </div>
                  {s.feedback && (
                    <div className="history-feedback-snippet">{s.feedback}</div>
                  )}
                </div>

                <div className="history-metrics-group">
                  <div className="metric-chip">
                    <span className="metric-label">Nội dung</span>
                    <strong className="metric-value">{s.content_score || 0}</strong>
                  </div>
                  <div className="metric-chip">
                    <span className="metric-label">Tự tin</span>
                    <strong className="metric-value">{s.confidence_avg || s.expression_score || 0}%</strong>
                  </div>
                  <div className="metric-chip">
                    <span className="metric-label">Căng thẳng</span>
                    <strong className="metric-value">{s.stress_avg || 0}%</strong>
                  </div>
                </div>

                <div className="history-score-col">
                  <div className="history-overall-badge">
                    <Award size={14} style={{ marginRight: 4 }} />
                    <span className="score-big">{s.overall_score}</span>
                    <span className="score-sub">/100</span>
                  </div>
                  <span className="history-view-link">
                    Xem chi tiết <ArrowRight size={13} />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
