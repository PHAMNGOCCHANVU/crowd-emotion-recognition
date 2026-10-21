import React, { useEffect, useState } from 'react';
import { User, Lock, LogOut, CheckCircle2, AlertCircle, Save } from 'lucide-react';
import { api } from '../services/api';

export default function ProfilePage({ user, onUserUpdated, onLogout }) {
  // State profile info
  const [fullName, setFullName] = useState(user?.full_name || user?.name || '');
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number || '');
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoMsg, setInfoMsg] = useState({ type: '', text: '' });

  // State password change
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdMsg, setPwdMsg] = useState({ type: '', text: '' });

  useEffect(() => {
    api.getUserProfile().then((data) => {
      if (data) {
        if (data.full_name) setFullName(data.full_name);
        if (data.phone_number) setPhoneNumber(data.phone_number);
      }
    });
  }, []);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setInfoMsg({ type: '', text: '' });
    if (fullName.trim().length < 2) {
      setInfoMsg({ type: 'error', text: 'Họ và tên cần có ít nhất 2 ký tự.' });
      return;
    }

    setInfoLoading(true);
    try {
      const updated = await api.updateUserProfile({
        full_name: fullName.trim(),
        phone_number: phoneNumber.trim(),
      });
      setInfoMsg({ type: 'success', text: 'Cập nhật thông tin cá nhân thành công!' });
      if (onUserUpdated) {
        onUserUpdated({ ...user, ...updated, full_name: fullName.trim() });
      }
    } catch (err) {
      setInfoMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Không thể cập nhật thông tin. Vui lòng thử lại.',
      });
    } finally {
      setInfoLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdMsg({ type: '', text: '' });

    if (!currentPassword) {
      setPwdMsg({ type: 'error', text: 'Vui lòng nhập mật khẩu hiện tại.' });
      return;
    }
    if (newPassword.length < 8) {
      setPwdMsg({ type: 'error', text: 'Mật khẩu mới phải có tối thiểu 8 ký tự.' });
      return;
    }
    if (newPassword === currentPassword) {
      setPwdMsg({ type: 'error', text: 'Mật khẩu mới không được trùng với mật khẩu hiện tại.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdMsg({ type: 'error', text: 'Xác nhận mật khẩu mới không khớp.' });
      return;
    }

    setPwdLoading(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      setPwdMsg({ type: 'success', text: 'Đổi mật khẩu thành công!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPwdMsg({
        type: 'error',
        text: err?.response?.data?.detail || 'Đổi mật khẩu thất bại. Mật khẩu hiện tại không đúng.',
      });
    } finally {
      setPwdLoading(false);
    }
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <div className="page-shell profile-container">
      <div style={{ marginBottom: 32 }}>
        <div className="eyebrow">Tài khoản & Thiết lập</div>
        <h1 className="page-title">Hồ sơ cá nhân</h1>
        <p className="page-subtitle">Quản lý thông tin định danh và bảo mật tài khoản luyện tập của bạn.</p>
      </div>

      <div className="profile-layout">
        {/* Cột trái: Thông tin cá nhân */}
        <div className="panel profile-card-main">
          <div className="profile-header-badge">
            <div className="profile-large-avatar">
              {getInitials(fullName || user?.email)}
            </div>
            <div>
              <h2 className="profile-name">{fullName || 'Ứng viên'}</h2>
              <div className="profile-meta-line">
                <span className="profile-role-tag">Candidate</span>
                <span className="profile-email-text">{user?.email}</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleUpdateProfile} className="profile-form">
            <h3 className="profile-section-title">
              <User size={16} /> Thông tin cá nhân
            </h3>

            {infoMsg.text && (
              <div className={`profile-alert ${infoMsg.type}`}>
                {infoMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                <span>{infoMsg.text}</span>
              </div>
            )}

            <div className="form-group">
              <label>Địa chỉ Email (Định danh)</label>
              <input type="email" value={user?.email || ''} disabled className="input-disabled" />
              <small className="form-hint">Email đăng nhập không thể thay đổi.</small>
            </div>

            <div className="form-group">
              <label>Họ và tên</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nhập họ và tên đầy đủ"
                required
              />
            </div>

            <div className="form-group">
              <label>Số điện thoại</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="Ví dụ: 0912345678"
              />
            </div>

            <button type="submit" className="primary-button profile-btn" disabled={infoLoading}>
              <Save size={15} /> {infoLoading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </form>
        </div>

        {/* Cột phải: Đổi mật khẩu & Đăng xuất */}
        <div className="profile-side-column">
          <div className="panel profile-card-pwd">
            <form onSubmit={handleChangePassword} className="profile-form">
              <h3 className="profile-section-title">
                <Lock size={16} /> Đổi mật khẩu
              </h3>

              {pwdMsg.text && (
                <div className={`profile-alert ${pwdMsg.type}`}>
                  {pwdMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                  <span>{pwdMsg.text}</span>
                </div>
              )}

              <div className="form-group">
                <label>Mật khẩu hiện tại</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="form-group">
                <label>Mật khẩu mới</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Tối thiểu 8 ký tự"
                  required
                />
              </div>

              <div className="form-group">
                <label>Xác nhận mật khẩu mới</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Nhập lại mật khẩu mới"
                  required
                />
              </div>

              <button type="submit" className="secondary-button profile-btn" disabled={pwdLoading}>
                {pwdLoading ? 'Đang cập nhật...' : 'Cập nhật mật khẩu'}
              </button>
            </form>
          </div>

          <div className="panel profile-card-logout">
            <h4 style={{ margin: '0 0 8px 0', fontSize: 15, fontWeight: 600, color: '#b91c1c' }}>
              Đăng xuất phiên làm việc
            </h4>
            <p style={{ margin: '0 0 16px 0', fontSize: 13, color: '#64748b' }}>
              Dọn dẹp phiên làm việc, tắt mọi camera tracks và quay về màn hình đăng nhập.
            </p>
            <button className="profile-logout-btn" onClick={onLogout}>
              <LogOut size={16} /> Đăng xuất tài khoản
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
