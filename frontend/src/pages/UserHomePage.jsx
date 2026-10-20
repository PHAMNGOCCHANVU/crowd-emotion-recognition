import React, { useEffect, useState } from 'react';
import {
  ArrowRight, BarChart3, BookOpen, Briefcase, Brain, LayoutTemplate, Megaphone,
  Network, PlayCircle, Route, Server, Target, TrendingUp, Users, CalendarCheck,
} from 'lucide-react';
import { api } from '../services/api';
import { LEVELS } from '../services/mockData';

const ICONS = {
  server: Server, layout: LayoutTemplate, chart: BarChart3, briefcase: Briefcase,
  brain: Brain, network: Network, trend: TrendingUp, megaphone: Megaphone, users: Users,
};

const levelLabel = (id) => LEVELS.find((l) => l.id === id)?.label || id;
const VISIBLE_COUNT = 6;

export default function UserHomePage({ user, onStartInterview, onOpenHistory }) {
  const [level, setLevel] = useState('');
  const [positions, setPositions] = useState([]);
  const [loadingPositions, setLoadingPositions] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    let cancelled = false;
    setLoadingPositions(true);
    api.getPositions({ level: level || undefined }).then((data) => {
      if (cancelled) return;
      setPositions(data);
      setLoadingPositions(false);
    });
    return () => { cancelled = true; };
  }, [level]);

  useEffect(() => {
    api.getRecentResults(3).then(setRecent);
  }, []);

  const quickActions = [
    { icon: PlayCircle, title: 'Bắt đầu phỏng vấn ngay', text: 'Chọn vị trí, mức độ và bắt đầu luyện tập với AI.', onClick: () => onStartInterview(), featured: true },
    { icon: BookOpen, title: 'Thư viện câu hỏi', text: 'Khám phá hàng ngàn câu hỏi phỏng vấn theo vị trí, kỹ năng.', onClick: () => onStartInterview() },
    { icon: BarChart3, title: 'Xem kết quả', text: 'Theo dõi tiến độ, điểm mạnh, điểm cần cải thiện.', onClick: onOpenHistory },
    { icon: Route, title: 'Lộ trình học tập', text: 'Cá nhân hóa lộ trình phù hợp với mục tiêu của bạn.', soon: true },
  ];

  const visiblePositions = showAll ? positions : positions.slice(0, VISIBLE_COUNT);

  const startWith = (position) => {
    const lv = level && position.levels.includes(level) ? level : position.levels[0];
    onStartInterview({ positionId: position.id, level: lv });
  };

  return (
    <div className="user-home">
      <h1 className="uh-greeting">Xin chào, {user?.name || 'bạn'} 👋</h1>
      <p className="page-subtitle">Hãy chọn vị trí và mức độ phù hợp để bắt đầu luyện tập phỏng vấn nhé!</p>

      <div className="uh-actions">
        {quickActions.map(({ icon: Icon, title, text, onClick, featured, soon }) => (
          <button
            key={title}
            className={`uh-action ${featured ? 'featured' : ''}`}
            onClick={onClick}
            disabled={soon}
          >
            <span className="uh-action-icon"><Icon size={18} /></span>
            <span className="uh-action-title">{title}</span>
            <span className="uh-action-text">{text}</span>
            {soon ? <span className="uh-soon">Sắp ra mắt</span> : <ArrowRight className="uh-action-arrow" size={15} />}
          </button>
        ))}
      </div>

      <div className="uh-columns">
        <section className="uh-card">
          <div className="uh-card-header">
            <h3><Target size={16} /> Vị trí phỏng vấn gợi ý</h3>
            {positions.length > VISIBLE_COUNT && (
              <button className="uh-link" onClick={() => setShowAll((v) => !v)}>
                {showAll ? 'Thu gọn' : 'Xem tất cả'} <ArrowRight size={12} />
              </button>
            )}
          </div>

          <div className="uh-chips">
            {[{ id: '', label: 'Tất cả' }, ...LEVELS].map((l) => (
              <button
                key={l.id || 'all'}
                className={`uh-chip ${level === l.id ? 'active' : ''}`}
                onClick={() => { setLevel(l.id); setShowAll(false); }}
              >
                {l.label}
              </button>
            ))}
          </div>

          {loadingPositions ? (
            <div className="uh-empty">Đang tải vị trí...</div>
          ) : visiblePositions.length === 0 ? (
            <div className="uh-empty">Chưa có vị trí phù hợp với mức độ này.</div>
          ) : (
            <div className="uh-positions">
              {visiblePositions.map((p) => {
                const Icon = ICONS[p.icon] || Briefcase;
                const tagLevel = level && p.levels.includes(level) ? level : p.levels[0];
                return (
                  <button key={p.id} className="uh-position" onClick={() => startWith(p)}>
                    <div className="uh-position-top">
                      <span className="uh-position-icon"><Icon size={16} /></span>
                      <span className="uh-position-title">{p.title}</span>
                      <ArrowRight size={14} className="uh-position-arrow" />
                    </div>
                    <div className="uh-tags">
                      <span className={`uh-tag lvl-${tagLevel}`}>{levelLabel(tagLevel)}</span>
                      {p.skills.map((s) => <span key={s} className="uh-tag">{s}</span>)}
                    </div>
                    <div className="uh-position-meta">{p.field} · {p.duration}</div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        <section className="uh-card">
          <div className="uh-card-header">
            <h3><CalendarCheck size={16} /> Kết quả gần đây</h3>
            <button className="uh-link" onClick={onOpenHistory}>Xem tất cả <ArrowRight size={12} /></button>
          </div>
          {recent.length === 0 ? (
            <div className="uh-empty">Bạn chưa có kết quả nào.</div>
          ) : (
            <div className="uh-results">
              {recent.map((r) => {
                const d = new Date(r.created_at);
                return (
                  <button key={r.session_id} className="uh-result" onClick={onOpenHistory}>
                    <span className="uh-date">
                      <strong>{d.getDate()}</strong>
                      <small>Th{String(d.getMonth() + 1).padStart(2, '0')}</small>
                    </span>
                    <span className="uh-result-info">
                      <span className="uh-result-title">Phỏng vấn vị trí: {r.role_name}</span>
                      <span className="uh-result-sub">
                        {levelLabel(r.level)} · {d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </span>
                    <span className="uh-score">{r.overall_score}<small>/100</small></span>
                  </button>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
