import React from 'react';
import { Users, Video, Clock, CheckCircle } from 'lucide-react';

export default function AdminDashboard() {
  const stats = [
    { title: 'Tổng ứng viên', value: '1,284', icon: Users, color: '#3b82f6' },
    { title: 'Phiên phỏng vấn', value: '342', icon: Video, color: '#8b5cf6' },
    { title: 'Thời gian AI đã chấm', value: '128h', icon: Clock, color: '#f59e0b' },
    { title: 'Tỷ lệ hoàn thành', value: '94%', icon: CheckCircle, color: '#10b981' },
  ];

  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', marginBottom: '24px' }}>Dashboard Tổng Quan</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '32px' }}>
        {stats.map((s, idx) => (
          <div key={idx} className="panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '12px', background: `${s.color}15`, color: s.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <s.icon size={28} />
            </div>
            <div>
              <div style={{ fontSize: '14px', color: '#64748b', fontWeight: 500, marginBottom: '4px' }}>{s.title}</div>
              <div style={{ fontSize: '24px', color: '#0f172a', fontWeight: 800 }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="panel" style={{ padding: '24px', height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fff' }}>
        <p style={{ color: '#94a3b8' }}>Biểu đồ thống kê phỏng vấn theo tháng (Sử dụng Chart.js / Recharts sau)</p>
      </div>
    </div>
  );
}