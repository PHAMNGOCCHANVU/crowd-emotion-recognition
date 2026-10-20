import React, { useEffect, useState } from 'react';
import { Bot, History as HistoryIcon } from 'lucide-react';
import { api } from '../services/api';
import AdvisorChat from '../components/AdvisorChat';

const LEVEL_LABEL = { intern: 'Intern', fresher: 'Fresher', junior: 'Junior', middle: 'Middle', senior: 'Senior' };
const formatDate = (iso) => new Date(iso).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });

export default function HistoryPage({ initialTab = 'sessions' }) {
  const [tab, setTab] = useState(initialTab);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.getSessionHistory().then((list) =>
      setSessions([...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
    );
  }, []);

  return (
    <div className="agent-page">
      <div className="eyebrow">Your activity</div>
      <h1 className="page-title">Lịch sử phỏng vấn</h1>
      <p className="page-subtitle">Theo dõi các phiên luyện tập và nhận lời khuyên từ AI dựa trên chính dữ liệu của bạn.</p>

      <div className="history-tabs">
        <button className={tab === 'sessions' ? 'active' : ''} onClick={() => setTab('sessions')}><HistoryIcon size={15} /> Phiên phỏng vấn</button>
        <button className={tab === 'ai' ? 'active' : ''} onClick={() => setTab('ai')}><Bot size={15} /> AI phân tích & tư vấn</button>
      </div>

      {tab === 'sessions' ? (
        <div className="history-list">
          {sessions.map((s) => (
            <div className="history-row history-row-detail" key={s.session_id}>
              <div>
                <div className="history-role">{s.role_name} <span className="history-level">{LEVEL_LABEL[s.level] || s.level}</span></div>
                <div className="history-date">{formatDate(s.created_at)}</div>
                {s.feedback && <div className="history-feedback">{s.feedback}</div>}
              </div>
              <div className="history-metrics">
                <span>Nội dung <b>{s.content_score}</b></span>
                <span>Giọng nói <b>{s.voice_score}</b></span>
                <span>Biểu cảm <b>{s.expression_score}</b></span>
              </div>
              <div className="history-score">{s.overall_score}<small>/100</small></div>
            </div>
          ))}
          {sessions.length === 0 && <div className="agent-empty">Bạn chưa có phiên phỏng vấn nào.</div>}
        </div>
      ) : (
        <AdvisorChat sessions={sessions} />
      )}
    </div>
  );
}
