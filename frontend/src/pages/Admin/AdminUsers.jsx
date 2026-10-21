import React, { useState, useEffect } from 'react';
import { Search, Eye, Trash2, X, RefreshCw, AlertCircle, Calendar, Mail, Phone, Award } from 'lucide-react';
import { api } from '../../services/api';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userSessions, setUserSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [actionError, setActionError] = useState(null);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadUsers = async (search) => {
    setLoading(true);
    setActionError(null);
    try {
      const data = await api.adminGetUsers(search);
      setUsers(data);
    } catch (err) {
      console.error('Lỗi nạp danh sách ứng viên:', err);
      setActionError('Không thể nạp danh sách ứng viên.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers(debouncedSearch);
  }, [debouncedSearch]);

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa ứng viên "${user.full_name}" (${user.email})? Mọi dữ liệu phỏng vấn liên quan sẽ bị xóa vĩnh viễn.`)) {
      return;
    }
    try {
      await api.adminDeleteUser(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
      if (selectedUser?.id === user.id) {
        setSelectedUser(null);
      }
    } catch (err) {
      console.error('Lỗi xóa ứng viên:', err);
      alert('Không thể xóa ứng viên. Vui lòng thử lại sau.');
    }
  };

  const handleViewDetails = async (user) => {
    setSelectedUser(user);
    setLoadingSessions(true);
    try {
      const sessions = await api.adminGetUserSessions(user.id);
      setUserSessions(sessions);
    } catch (err) {
      console.error('Lỗi nạp chi tiết phiên phỏng vấn:', err);
      setUserSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Quản lý Ứng viên</h1>
          <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0 0' }}>Theo dõi danh sách ứng viên và kết quả phỏng vấn AI thực tế.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', background: '#fff', border: '1px solid #e2e8f0', padding: '8px 16px', borderRadius: '8px', width: '320px' }}>
            <Search size={18} color="#94a3b8" style={{ marginRight: '8px' }} />
            <input
              type="text"
              placeholder="Tìm theo tên hoặc email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ border: 'none', outline: 'none', fontSize: '14px', width: '100%' }}
            />
          </div>
          <button
            onClick={() => loadUsers(debouncedSearch)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              background: '#fff',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              color: '#475569',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Làm mới
          </button>
        </div>
      </div>

      {actionError && (
        <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <AlertCircle size={16} />
          <span style={{ fontSize: '14px' }}>{actionError}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="panel" style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>HỌ TÊN & EMAIL</th>
              <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>SỐ ĐIỆN THOẠI</th>
              <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>SỐ BUỔI PHỎNG VẤN</th>
              <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>ĐIỂM TRUNG BÌNH</th>
              <th style={{ padding: '14px 20px', textAlign: 'right' }}>THAO TÁC</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="5" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                  Đang tải danh sách ứng viên...
                </td>
              </tr>
            ) : users.length > 0 ? (
              users.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 20px' }}>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{u.full_name}</div>
                    <div style={{ fontSize: '13px', color: '#64748b' }}>{u.email}</div>
                  </td>
                  <td style={{ padding: '14px 20px', fontSize: '14px', color: '#475569' }}>
                    {u.phone_number || '---'}
                  </td>
                  <td style={{ padding: '14px 20px', fontSize: '14px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 10px',
                      borderRadius: '12px',
                      background: '#eff6ff',
                      color: '#2563eb',
                      fontWeight: 600,
                      fontSize: '12px',
                    }}>
                      {u.session_count || 0} phiên
                    </span>
                  </td>
                  <td style={{ padding: '14px 20px' }}>
                    <span style={{
                      fontWeight: 700,
                      color: u.average_score >= 70 ? '#10b981' : u.average_score > 0 ? '#f59e0b' : '#94a3b8',
                      fontSize: '14px',
                    }}>
                      {u.average_score > 0 ? `${u.average_score}/100` : 'Chưa có'}
                    </span>
                  </td>
                  <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                      <button
                        onClick={() => handleViewDetails(u)}
                        title="Xem chi tiết & Lịch sử"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          background: '#f8fafc',
                          border: '1px solid #e2e8f0',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          color: '#3b82f6',
                          cursor: 'pointer',
                          fontSize: '13px',
                          fontWeight: 500,
                        }}
                      >
                        <Eye size={14} /> Chi tiết
                      </button>
                      <button
                        onClick={() => handleDeleteUser(u)}
                        title="Xóa ứng viên"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          background: '#fef2f2',
                          border: '1px solid #fecaca',
                          padding: '6px 10px',
                          borderRadius: '6px',
                          color: '#ef4444',
                          cursor: 'pointer',
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                  {debouncedSearch ? 'Không tìm thấy ứng viên nào phù hợp với từ khóa.' : 'Chưa có ứng viên nào.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* MODAL CHI TIẾT ỨNG VIÊN */}
      {selectedUser && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px',
        }}>
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '720px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
          }}>
            {/* Header Modal */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Hồ sơ & Lịch sử phỏng vấn</h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>Ứng viên: <strong>{selectedUser.full_name}</strong></p>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Nội dung Modal */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              {/* Thẻ tóm tắt thông tin */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b', fontSize: '12px', marginBottom: '4px' }}>
                    <Mail size={14} /> Email
                  </div>
                  <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '13px', wordBreak: 'break-all' }}>{selectedUser.email}</div>
                </div>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b', fontSize: '12px', marginBottom: '4px' }}>
                    <Phone size={14} /> Số điện thoại
                  </div>
                  <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '13px' }}>{selectedUser.phone_number || 'Chưa cập nhật'}</div>
                </div>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b', fontSize: '12px', marginBottom: '4px' }}>
                    <Award size={14} /> Điểm trung bình
                  </div>
                  <div style={{ fontWeight: 700, color: '#10b981', fontSize: '14px' }}>
                    {selectedUser.average_score > 0 ? `${selectedUser.average_score}/100` : '---'}
                  </div>
                </div>
              </div>

              {/* Lịch sử phiên phỏng vấn */}
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a', margin: '0 0 12px 0' }}>
                Các phiên phỏng vấn đã tham gia
              </h4>

              {loadingSessions ? (
                <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>Đang nạp dữ liệu phiên phỏng vấn...</div>
              ) : userSessions.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                      <th style={{ padding: '10px 12px', color: '#475569', fontWeight: 600 }}>VỊ TRÍ</th>
                      <th style={{ padding: '10px 12px', color: '#475569', fontWeight: 600 }}>CẤP ĐỘ</th>
                      <th style={{ padding: '10px 12px', color: '#475569', fontWeight: 600 }}>THỜI GIAN</th>
                      <th style={{ padding: '10px 12px', color: '#475569', fontWeight: 600 }}>TRẠNG THÁI</th>
                      <th style={{ padding: '10px 12px', color: '#475569', fontWeight: 600, textAlign: 'right' }}>ĐIỂM SỐ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userSessions.map((s, idx) => (
                      <tr key={s.session_id || idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: '#0f172a' }}>{s.role_name}</td>
                        <td style={{ padding: '10px 12px', color: '#64748b' }}>{s.level}</td>
                        <td style={{ padding: '10px 12px', color: '#64748b' }}>{s.created_at}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '10px',
                            fontSize: '11px',
                            fontWeight: 600,
                            background: s.status === 'COMPLETED' ? '#dcfce7' : '#fef3c7',
                            color: s.status === 'COMPLETED' ? '#166534' : '#92400e',
                          }}>
                            {s.status === 'COMPLETED' ? 'Hoàn thành' : 'Đang làm'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 700, color: s.overall_score >= 70 ? '#10b981' : '#f59e0b' }}>
                          {s.overall_score > 0 ? `${s.overall_score}/100` : '---'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8', background: '#f8fafc', borderRadius: '8px' }}>
                  Ứng viên này chưa hoàn thành phiên phỏng vấn nào.
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div style={{ padding: '16px 24px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end', background: '#f8fafc' }}>
              <button
                onClick={() => setSelectedUser(null)}
                style={{
                  padding: '8px 16px',
                  background: '#e2e8f0',
                  color: '#475569',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
