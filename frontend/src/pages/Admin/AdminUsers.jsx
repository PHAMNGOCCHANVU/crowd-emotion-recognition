import React, { useState } from 'react';
import { Search, MoreVertical, Edit, Trash2, Eye } from 'lucide-react';

const initialUsers = [
  { id: 1, name: 'Nguyễn Văn A', email: 'a.nguyen@email.com', role: 'Software Engineer', date: '2026-10-12', score: '85/100' },
  { id: 2, name: 'Trần Thị B', email: 'b.tran@email.com', role: 'Data Analyst', date: '2026-10-10', score: '72/100' },
  { id: 3, name: 'Lê Hoàng C', email: 'c.le@email.com', role: 'Marketing', date: '2026-10-09', score: 'Đang chấm...' },
  { id: 4, name: 'Phạm Minh D', email: 'd.pham@email.com', role: 'Sales / Business Development', date: '2026-10-11', score: '90/100' },
  { id: 5, name: 'Đặng Nam', email: 'nam.dang@email.com', role: 'Human Resources (HR)', date: '2026-10-13', score: 'Đang chấm...' },
];

export default function AdminUsers() {
  const [users, setUsers] = useState(initialUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeMenuId, setActiveMenuId] = useState(null);

  const filteredUsers = users.filter(user => 
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDelete = (id) => {
    if (window.confirm('Bạn có chắc chắn muốn xóa ứng viên này?')) {
      setUsers(users.filter(u => u.id !== id));
      setActiveMenuId(null);
    }
  };

  return (
    <div onClick={() => setActiveMenuId(null)}> {/* Click ra ngoài để đóng menu */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Quản lý Ứng viên</h1>
        <div style={{ display: 'flex', alignItems: 'center', background: '#fff', border: '1px solid #e2e8f0', padding: '8px 16px', borderRadius: '8px', width: '300px' }}>
          <Search size={18} color="#94a3b8" style={{ marginRight: '8px' }} />
          <input 
            type="text" 
            placeholder="Tìm theo tên hoặc email..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ border: 'none', outline: 'none', fontSize: '14px', width: '100%' }} 
          />
        </div>
      </div>

      <div className="panel" style={{ overflow: 'visible' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '16px 24px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>HỌ TÊN</th>
              <th style={{ padding: '16px 24px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>VỊ TRÍ ỨNG TUYỂN</th>
              <th style={{ padding: '16px 24px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>NGÀY PHỎNG VẤN</th>
              <th style={{ padding: '16px 24px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>ĐIỂM AI ĐÁNH GIÁ</th>
              <th style={{ padding: '16px 24px' }}></th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.length > 0 ? filteredUsers.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '16px 24px' }}>
                  <div style={{ fontWeight: 600, color: '#0f172a' }}>{u.name}</div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>{u.email}</div>
                </td>
                <td style={{ padding: '16px 24px', fontSize: '14px' }}>{u.role}</td>
                <td style={{ padding: '16px 24px', fontSize: '14px', color: '#475569' }}>{u.date}</td>
                <td style={{ padding: '16px 24px', fontWeight: 600, color: u.score.includes('Đang') ? '#f59e0b' : '#10b981' }}>{u.score}</td>
                <td style={{ padding: '16px 24px', textAlign: 'right', position: 'relative' }}>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setActiveMenuId(activeMenuId === u.id ? null : u.id); }}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px' }}
                  >
                    <MoreVertical size={18} />
                  </button>
                  
                  {/* Menu Dropdown */}
                  {activeMenuId === u.id && (
                    <div style={{ position: 'absolute', right: '40px', top: '30px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 10, width: '160px', overflow: 'hidden' }}>
                      <button onClick={() => alert(`Xem chi tiết: ${u.name}`)} style={{ width: '100%', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '8px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', fontSize: '13px', color: '#475569' }}>
                        <Eye size={14} /> Xem chi tiết
                      </button>
                      <button onClick={() => alert(`Chỉnh sửa: ${u.name}`)} style={{ width: '100%', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '8px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', fontSize: '13px', color: '#475569' }}>
                        <Edit size={14} /> Chỉnh sửa
                      </button>
                      <button onClick={() => handleDelete(u.id)} style={{ width: '100%', padding: '10px 16px', display: 'flex', alignItems: 'center', gap: '8px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', fontSize: '13px', color: '#ef4444', borderTop: '1px solid #f1f5f9' }}>
                        <Trash2 size={14} /> Xóa ứng viên
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            )) : (
              <tr><td colSpan="5" style={{ padding: '32px', textAlign: 'center', color: '#94a3b8' }}>Không tìm thấy ứng viên nào phù hợp.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}