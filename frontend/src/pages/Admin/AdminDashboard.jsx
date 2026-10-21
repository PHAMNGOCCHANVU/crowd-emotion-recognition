import React, { useEffect, useState } from 'react';
import { Users, Video, Award, CheckCircle, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';

export default function AdminDashboard() {
  const [statsData, setStatsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.adminGetStats();
      setStatsData(data);
    } catch (err) {
      console.error('Lỗi nạp thống kê dashboard:', err);
      setError('Không thể tải dữ liệu thống kê từ hệ thống.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const stats = [
    {
      title: 'Tổng ứng viên',
      value: statsData?.total_users != null ? statsData.total_users.toLocaleString() : '---',
      icon: Users,
      color: '#3b82f6',
    },
    {
      title: 'Phiên phỏng vấn',
      value: statsData?.total_sessions != null ? statsData.total_sessions.toLocaleString() : '---',
      icon: Video,
      color: '#8b5cf6',
    },
    {
      title: 'Tỷ lệ hoàn thành',
      value: statsData?.completion_rate != null ? `${statsData.completion_rate}%` : '---',
      icon: CheckCircle,
      color: '#10b981',
    },
    {
      title: 'Điểm trung bình',
      value: statsData?.average_score != null ? `${statsData.average_score}/100` : '---',
      icon: Award,
      color: '#f59e0b',
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Dashboard Tổng Quan</h1>
          <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0 0' }}>Số liệu hoạt động phỏng vấn trực tiếp từ cơ sở dữ liệu.</p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: '#fff',
            border: '1px solid #e2e8f0',
            padding: '8px 16px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            color: '#475569',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Đang cập nhật...' : 'Làm mới'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px 18px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '10px', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
          <AlertCircle size={18} />
          <span style={{ fontSize: '14px' }}>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '28px' }}>
        {stats.map((s, idx) => (
          <div key={idx} className="panel" style={{ padding: '22px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '52px', height: '52px', borderRadius: '12px', background: `${s.color}15`, color: s.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <s.icon size={26} />
            </div>
            <div>
              <div style={{ fontSize: '13px', color: '#64748b', fontWeight: 500, marginBottom: '4px' }}>{s.title}</div>
              <div style={{ fontSize: '22px', color: '#0f172a', fontWeight: 800 }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Hoạt động phỏng vấn gần đây */}
      <div className="panel" style={{ padding: '24px', background: '#fff' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
          Hoạt động phỏng vấn gần đây
        </h3>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Đang nạp dữ liệu hoạt động gần đây...</div>
        ) : statsData?.recent_sessions && statsData.recent_sessions.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>ỨNG VIÊN</th>
                <th style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>VỊ TRÍ</th>
                <th style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>NGÀY</th>
                <th style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>TRẠNG THÁI</th>
                <th style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px', fontWeight: 600, textAlign: 'right' }}>ĐIỂM SỐ</th>
              </tr>
            </thead>
            <tbody>
              {statsData.recent_sessions.map((item, idx) => (
                <tr key={item.session_id || idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#0f172a' }}>{item.candidate_name}</td>
                  <td style={{ padding: '14px 16px', fontSize: '14px', color: '#475569' }}>{item.role}</td>
                  <td style={{ padding: '14px 16px', fontSize: '14px', color: '#64748b' }}>{item.date}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 10px',
                      borderRadius: '16px',
                      fontSize: '12px',
                      fontWeight: 600,
                      background: item.status === 'Hoàn thành' ? '#dcfce7' : '#fef3c7',
                      color: item.status === 'Hoàn thành' ? '#166534' : '#92400e',
                    }}>
                      {item.status}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: item.score >= 70 ? '#10b981' : item.score > 0 ? '#f59e0b' : '#94a3b8' }}>
                    {item.score > 0 ? `${item.score}/100` : '---'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
            Chưa có phiên phỏng vấn nào gần đây.
          </div>
        )}
      </div>
    </div>
  );
}
