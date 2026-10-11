import React, { useState } from 'react';
import { ArrowRight, LogIn, UserPlus } from 'lucide-react';
import { api } from '../services/api';

export default function AuthPage({ mode = 'login', onAuthenticated, onModeChange }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('demo@interviewlab.test');
  const [password, setPassword] = useState('123456');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isLogin = mode === 'login';
  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      const user = isLogin
        ? await api.login(email, password)
        : await api.register(name, email, password);
      onAuthenticated(user);
    } catch (err) {
      setError(err.message || 'Không thể thực hiện yêu cầu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-intro">
        <div className="eyebrow">InterviewLab</div>
        <h1>Luyện tập để tự tin hơn trong mỗi cuộc phỏng vấn.</h1>
        <p>Nhận phản hồi đa chiều về câu trả lời, giọng nói và phong thái của bạn.</p>
      </div>
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-icon">{isLogin ? <LogIn size={20} /> : <UserPlus size={20} />}</div>
        <div className="eyebrow">{isLogin ? 'Welcome back' : 'Get started'}</div>
        <h2>{isLogin ? 'Đăng nhập' : 'Tạo tài khoản'}</h2>
        <p className="auth-hint">{isLogin ? 'Đăng nhập để tiếp tục phiên luyện tập.' : 'Tạo tài khoản miễn phí để lưu lịch sử.'}</p>
        {!isLogin && <input className="auth-input" placeholder="Họ và tên" value={name} onChange={(e) => setName(e.target.value)} required />}
        <input className="auth-input" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="auth-input" type="password" placeholder="Mật khẩu" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <div className="auth-error">{error}</div>}
        <button className="primary-button auth-submit" disabled={loading}>{loading ? 'Đang xử lý...' : isLogin ? 'Đăng nhập' : 'Đăng ký'} <ArrowRight size={16} /></button>
        <button type="button" className="auth-switch" onClick={() => onModeChange(isLogin ? 'register' : 'login')}>
          {isLogin ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập'}
        </button>
      </form>
    </div>
  );
}
