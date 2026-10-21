import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  BarChart3,
  Briefcase,
  Brain,
  ChevronLeft,
  ChevronRight,
  LayoutTemplate,
  Megaphone,
  Network,
  Server,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react';
import { api } from '../services/api';
import { LEVELS } from '../services/mockData';

const ICONS = {
  server: Server,
  layout: LayoutTemplate,
  chart: BarChart3,
  briefcase: Briefcase,
  brain: Brain,
  network: Network,
  trend: TrendingUp,
  megaphone: Megaphone,
  users: Users,
};

const levelLabel = (id) => LEVELS.find((l) => l.id === id)?.label || id;
const ITEMS_PER_PAGE = 4;
const WINDOW_SIZE = 4;

export default function UserHomePage({ user, onStartInterview }) {
  const [level, setLevel] = useState('');
  const [positions, setPositions] = useState([]);
  const [loadingPositions, setLoadingPositions] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [windowStart, setWindowStart] = useState(1);

  useEffect(() => {
    let cancelled = false;
    setLoadingPositions(true);
    api.getPositions({ level: level || undefined }).then((data) => {
      if (cancelled) return;
      setPositions(data || []);
      setLoadingPositions(false);
      setCurrentPage(1);
      setWindowStart(1);
    });
    return () => {
      cancelled = true;
    };
  }, [level]);

  // Phân trang
  const totalPages = Math.max(1, Math.ceil(positions.length / ITEMS_PER_PAGE));

  // Điều chỉnh windowStart khi totalPages thay đổi
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [totalPages, currentPage]);

  const displayedPages = useMemo(() => {
    const pages = [];
    const end = Math.min(totalPages, windowStart + WINDOW_SIZE - 1);
    for (let i = windowStart; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  }, [windowStart, totalPages]);

  const handlePrevWindow = () => {
    const nextStart = Math.max(1, windowStart - 1);
    setWindowStart(nextStart);
    if (currentPage > nextStart + WINDOW_SIZE - 1) {
      setCurrentPage(nextStart + WINDOW_SIZE - 1);
    } else if (currentPage < nextStart) {
      setCurrentPage(nextStart);
    }
  };

  const handleNextWindow = () => {
    const maxStart = Math.max(1, totalPages - WINDOW_SIZE + 1);
    const nextStart = Math.min(maxStart, windowStart + 1);
    setWindowStart(nextStart);
    if (currentPage < nextStart) {
      setCurrentPage(nextStart);
    } else if (currentPage > nextStart + WINDOW_SIZE - 1) {
      setCurrentPage(nextStart + WINDOW_SIZE - 1);
    }
  };

  const paginatedPositions = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return positions.slice(start, start + ITEMS_PER_PAGE);
  }, [positions, currentPage]);

  const startWith = (position) => {
    const lv = level && position.levels.includes(level) ? level : position.levels[0];
    onStartInterview({ positionId: position.id, level: lv });
  };

  return (
    <div className="user-home full-width">
      {/* Tiêu đề & Lời chào */}
      <div className="uh-greeting-section">
        <h1 className="uh-greeting">Xin chào, {user?.name || user?.full_name || 'bạn'} 👋</h1>
        <p className="page-subtitle">
          Khám phá danh sách các vị trí tuyển dụng gợi ý và bắt đầu phiên phỏng vấn thử nghiệm ngay hôm nay.
        </p>
      </div>

      {/* Vị trí phỏng vấn gợi ý (Full-width, Grid 4 card) */}
      <section className="panel uh-main-panel">
        <div className="uh-panel-header">
          <div className="uh-header-left">
            <h3>
              <Target size={18} /> Vị trí phỏng vấn gợi ý
            </h3>
            <span className="uh-total-badge">{positions.length} vị trí</span>
          </div>

          {/* Level Filter Chips */}
          <div className="uh-chips">
            {[{ id: '', label: 'Tất cả' }, ...LEVELS].map((l) => (
              <button
                key={l.id || 'all'}
                className={`uh-chip ${level === l.id ? 'active' : ''}`}
                onClick={() => setLevel(l.id)}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Danh sách 4 Cards / Hàng */}
        {loadingPositions ? (
          <div className="uh-empty">Đang tải danh sách vị trí...</div>
        ) : paginatedPositions.length === 0 ? (
          <div className="uh-empty">Chưa có vị trí phù hợp với mức độ này.</div>
        ) : (
          <div className="uh-grid-4">
            {paginatedPositions.map((p) => {
              const Icon = ICONS[p.icon] || Briefcase;
              const tagLevel = level && p.levels.includes(level) ? level : p.levels[0];
              return (
                <div
                  key={p.id}
                  className="uh-position-card"
                  onClick={() => startWith(p)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="uh-card-top">
                    <span className="uh-card-icon"><Icon size={18} /></span>
                    <span className={`uh-tag lvl-${tagLevel}`}>{levelLabel(tagLevel)}</span>
                  </div>

                  <h4 className="uh-card-title">{p.title}</h4>
                  <div className="uh-card-field">{p.field} · {p.duration}</div>

                  <div className="uh-card-skills">
                    {p.skills.slice(0, 3).map((s) => (
                      <span key={s} className="uh-skill-tag">{s}</span>
                    ))}
                    {p.skills.length > 3 && (
                      <span className="uh-skill-tag">+{p.skills.length - 3}</span>
                    )}
                  </div>

                  <div className="uh-card-bottom">
                    <span className="uh-card-cta">Bắt đầu luyện tập</span>
                    <ArrowRight size={14} className="uh-card-arrow" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Sliding Window Pagination: << [1, 2, 3, 4] >> */}
        {totalPages > 1 && (
          <div className="sliding-pagination">
            <button
              className="page-nav-btn"
              onClick={handlePrevWindow}
              disabled={windowStart <= 1 && currentPage <= 1}
              title="Trang trước"
            >
              <ChevronLeft size={16} />
            </button>

            <div className="page-numbers-group">
              {displayedPages.map((pageNum) => (
                <button
                  key={pageNum}
                  className={`page-num-btn ${currentPage === pageNum ? 'active' : ''}`}
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </button>
              ))}
            </div>

            <button
              className="page-nav-btn"
              onClick={handleNextWindow}
              disabled={
                windowStart + WINDOW_SIZE - 1 >= totalPages && currentPage >= totalPages
              }
              title="Trang tiếp"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
