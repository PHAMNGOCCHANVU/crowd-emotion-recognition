import React from 'react';
import { LayoutDashboard, Users, Briefcase, LogOut } from 'lucide-react';
import AdminDashboard from './AdminDashboard';
import AdminUsers from './AdminUsers';
import AdminInterviews from './AdminInterviews';

export default function AdminLayout({ currentRoute, onNavigate }) {
  const navItems = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Quản lý Ứng viên', path: '/admin/users', icon: Users },
    { name: 'Quản lý Phỏng vấn', path: '/admin/interviews', icon: Briefcase },
  ];

  // Ham render noi dung cho cac route hien tai
  const renderContent = () => {
    if (currentRoute === '/admin/users') return <AdminUsers />;
    if (currentRoute === '/admin/interviews') return <AdminInterviews />;
    return <AdminDashboard />;
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      {/* Sidebar */}
      <div style={{ width: '260px', background: '#0f172a', color: '#fff', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px', fontSize: '20px', fontWeight: 800, borderBottom: '1px solid #1e293b', color: '#38bdf8' }}>
          InterviewLab Admin
        </div>
        <div style={{ flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {navItems.map((item) => {
            const isActive = currentRoute === item.path;
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
                  borderRadius: '8px', fontSize: '15px', fontWeight: 500, border: 'none', cursor: 'pointer',
                  background: isActive ? '#1e293b' : 'transparent',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  transition: 'all 0.2s', textAlign: 'left', width: '100%'
                }}
              >
                <item.icon size={18} />
                {item.name}
              </button>
            );
          })}
        </div>
        <div style={{ padding: '16px 12px', borderTop: '1px solid #1e293b' }}>
          <button 
            onClick={() => onNavigate('/')}
            style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: '15px', fontWeight: 500 }}
          >
            <LogOut size={18} /> Về trang chủ Client
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{ height: '70px', background: '#fff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', padding: '0 32px', justifyContent: 'flex-end' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '14px', fontWeight: 600, color: '#475569' }}>Admin Manager</span>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: '#3b82f6', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>A</div>
          </div>
        </header>
        <main style={{ flex: 1, padding: '32px', overflowY: 'auto' }}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
}