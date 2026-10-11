import React, { useEffect, useState } from 'react';
import SetupPage from './pages/SetupPage';
import InterviewRoom from './pages/InterviewRoom';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import { Mic2, Home, Video, History, UserRound, Sparkles, ChevronRight } from 'lucide-react';

export default function App() {
  const initialPath = window.location.pathname;
  const [route, setRoute] = useState(initialPath);
  const [currentPage, setCurrentPage] = useState(initialPath === '/results' ? 'dashboard' : 'setup'); // 'setup' | 'interview' | 'dashboard'
  const [sessionData, setSessionData] = useState(null);
  const [cameraStream, setCameraStream] = useState(null);
  const [recordedBlobs, setRecordedBlobs] = useState({});
  const [activeSection, setActiveSection] = useState('interview');
  const [publicPage, setPublicPage] = useState(initialPath === '/register' ? 'register' : initialPath === '/login' ? 'login' : 'home');
  const [user, setUser] = useState(null);

  useEffect(() => {
    const handlePopState = () => setRoute(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setRoute(path);
  };

  const handleStartInterview = (session, stream) => {
    setSessionData(session);
    setCameraStream(stream);
    setCurrentPage('interview');
    setActiveSection('interview');
    navigate('/interview');
  };

  const handleFinishInterview = (sessionId, blobsMap) => {
    setRecordedBlobs(blobsMap);
    // Tắt camera khi đã phỏng vấn xong
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
    setCurrentPage('dashboard');
    setActiveSection('interview');
    navigate('/results');
  };

  const handleRestart = () => {
    setSessionData(null);
    setRecordedBlobs({});
    setCurrentPage('setup');
    setActiveSection('interview');
    navigate('/interview');
  };

  const handleNavigation = (section) => {
    setActiveSection(section);
    if (section === 'interview') {
      setCurrentPage('setup');
      setSessionData(null);
      setRecordedBlobs({});
      navigate('/interview');
    } else {
      navigate(`/${section}`);
    }
  };

  const renderSection = () => {
    if (activeSection === 'history') {
      return (
        <div className="empty-page">
          <div className="eyebrow">Your activity</div>
          <h1 className="page-title">Lịch sử phỏng vấn</h1>
          <p className="page-subtitle">Theo dõi những phiên luyện tập gần đây của bạn.</p>
          <div className="history-list">
            {[
              ['Software Engineer', '11/10/2026 · 10:32', '85'],
              ['Data Analyst', '08/10/2026 · 16:18', '78'],
              ['Product Marketing', '04/10/2026 · 09:45', '82'],
            ].map(([role, date, score]) => (
              <div className="history-row" key={`${role}-${date}`}>
                <div><div className="history-role">{role}</div><div className="history-date">{date}</div></div>
                <div className="history-score">{score}<small>/100</small></div>
              </div>
            ))}
          </div>
        </div>
      );
    }
    if (activeSection === 'profile') {
      return (
        <div className="empty-page">
          <div className="eyebrow">Account</div>
          <h1 className="page-title">Hồ sơ cá nhân</h1>
          <p className="page-subtitle">Thông tin dùng cho các phiên luyện tập của bạn.</p>
          <div className="profile-card">
            <div className="profile-avatar">ND</div>
            <div><div className="history-role">Nguyễn Minh Đức</div><div className="history-date">Ứng viên · Thành viên từ tháng 10/2026</div></div>
          </div>
        </div>
      );
    }
    if (activeSection === 'home') {
      return (
        <div className="empty-page">
          <div className="eyebrow">Welcome back</div>
          <h1 className="page-title">Sẵn sàng cho phiên luyện tập tiếp theo?</h1>
          <p className="page-subtitle">Luyện tập với câu hỏi phù hợp vị trí và nhận phản hồi đa chiều từ AI.</p>
          <button className="primary-button" style={{ marginTop: 24 }} onClick={() => handleNavigation('interview')}>Bắt đầu phỏng vấn <ChevronRight size={15} style={{ verticalAlign: 'middle' }} /></button>
        </div>
      );
    }
    if (currentPage === 'setup') return <SetupPage onStartInterview={handleStartInterview} />;
    if (currentPage === 'interview' && sessionData) return <InterviewRoom session={sessionData} stream={cameraStream} onFinishInterview={handleFinishInterview} />;
    if (currentPage === 'dashboard' && sessionData) return <DashboardPage sessionId={sessionData.session_id} blobsMap={recordedBlobs} onRestart={handleRestart} />;
    return null;
  };

  const navItems = [
    ['home', 'Trang chủ', Home],
    ['interview', 'Phỏng vấn', Video],
    ['history', 'Lịch sử', History],
    ['profile', 'Hồ sơ', UserRound],
  ];

  if (!user) {
    if (route === '/' || route === '/home') return <><header className="app-header public-header"><div className="brand"><span className="brand-mark"><Mic2 size={18} /></span><span>InterviewLab</span></div><div className="public-actions"><button className="auth-link" onClick={() => { setPublicPage('login'); navigate('/login'); }}>Đăng nhập</button><button className="primary-button" onClick={() => { setPublicPage('register'); navigate('/register'); }}>Đăng ký</button></div></header><HomePage onLogin={() => { setPublicPage('login'); navigate('/login'); }} onRegister={() => { setPublicPage('register'); navigate('/register'); }} /></>;
    return <><header className="app-header public-header"><div className="brand"><span className="brand-mark"><Mic2 size={18} /></span><span>InterviewLab</span></div><button className="auth-link" onClick={() => { setPublicPage('home'); navigate('/'); }}>Trang chủ</button></header><AuthPage mode={route === '/register' ? 'register' : 'login'} onModeChange={(mode) => { setPublicPage(mode); navigate(`/${mode}`); }} onAuthenticated={(nextUser) => { setUser(nextUser); setActiveSection('interview'); setCurrentPage('setup'); navigate('/interview'); }} /></>;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand"><span className="brand-mark"><Mic2 size={18} /></span><span>InterviewLab</span></div>
        <div className="header-meta">Phân tích đa phương thức · FER · Whisper · Gemini</div>
      </header>

      <div className="app-layout">
        <aside className="sidebar">
          <p className="sidebar-label">Workspace</p>
          <nav className="sidebar-nav">
            {navItems.map(([id, label, Icon]) => (
              <button key={id} className={`sidebar-item ${activeSection === id ? 'active' : ''}`} onClick={() => handleNavigation(id)}>
                <Icon size={17} /><span>{label}</span>
              </button>
            ))}
          </nav>
          <div className="sidebar-note"><Sparkles size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} /> AI phân tích giúp bạn cải thiện từng câu trả lời.</div>
        </aside>
        <main className="main-content">{renderSection()}</main>
      </div>
    </div>
  );
}
