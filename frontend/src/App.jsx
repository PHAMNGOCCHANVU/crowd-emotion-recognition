import React, { useEffect, useState } from 'react';
import SetupPage from './pages/SetupPage';
import InterviewRoom from './pages/InterviewRoom';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import UserHomePage from './pages/UserHomePage';
import HistoryPage from './pages/HistoryPage';
import { Mic2, Home, Video, History, UserRound, Sparkles, LogOut } from 'lucide-react';
import AdminLayout from './pages/Admin/AdminLayout';

export default function App() {
  const initialPath = window.location.pathname;
  const [route, setRoute] = useState(initialPath);
  const [currentPage, setCurrentPage] = useState(initialPath.startsWith('/results') ? 'dashboard' : 'setup'); // 'setup' | 'interview' | 'dashboard'
  
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('interviewlab_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [sessionData, setSessionData] = useState(() => {
    try {
      const saved = localStorage.getItem('interviewlab_current_session');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [cameraStream, setCameraStream] = useState(null);
  const [recordedBlobs, setRecordedBlobs] = useState({});
  const [activeSection, setActiveSection] = useState('home');
  const [interviewPreset, setInterviewPreset] = useState(null);
  const [, setPublicPage] = useState(initialPath === '/register' ? 'register' : initialPath === '/login' ? 'login' : 'home');

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      setRoute(path);
      if (path.startsWith('/results')) {
        setCurrentPage('dashboard');
        setActiveSection('interview');
      } else if (path === '/history') {
        setActiveSection('history');
      } else if (path === '/profile') {
        setActiveSection('profile');
      } else if (path === '/interview') {
        setActiveSection('interview');
      } else if (path === '/home' || path === '/') {
        setActiveSection('home');
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setRoute(path);
  };

  const handleLogout = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
    try {
      localStorage.removeItem('interviewlab_user');
      localStorage.removeItem('interviewlab_current_session');
    } catch (e) {}
    setUser(null);
    setSessionData(null);
    setCameraStream(null);
    setRecordedBlobs({});
    setCurrentPage('setup');
    setActiveSection('home');
    navigate('/login');
  };

  const handleStartInterview = (session, stream) => {
    setSessionData(session);
    setCameraStream(stream);
    try {
      localStorage.setItem('interviewlab_current_session', JSON.stringify(session));
      if (session?.session_id) {
        localStorage.setItem('interviewlab_last_session_id', session.session_id);
      }
    } catch (e) {
      console.warn(e);
    }
    setCurrentPage('interview');
    setActiveSection('interview');
    navigate('/interview');
  };

  const handleFinishInterview = (sessionId, blobsMap) => {
    setRecordedBlobs(blobsMap);
    // Tắt camera khi đã phỏng vấn xong để giải phóng thiết bị
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
    try {
      localStorage.setItem('interviewlab_last_session_id', sessionId);
    } catch (e) {}
    setCurrentPage('dashboard');
    setActiveSection('interview');
    navigate(`/results?session_id=${sessionId}`);
  };

  const handleRestart = () => {
    setSessionData(null);
    setRecordedBlobs({});
    try {
      localStorage.removeItem('interviewlab_current_session');
    } catch (e) {}
    setCurrentPage('setup');
    setActiveSection('interview');
    navigate('/interview');
  };

  const handleNavigation = (section) => {
    setActiveSection(section);
    if (section === 'interview') {
      setInterviewPreset(null);
      setCurrentPage('setup');
      setSessionData(null);
      setRecordedBlobs({});
      try {
        localStorage.removeItem('interviewlab_current_session');
      } catch (e) {}
      navigate('/interview');
    } else {
      navigate(`/${section}`);
    }
  };

  const handleStartFromHome = (preset = null) => {
    setActiveSection('interview');
    setCurrentPage('setup');
    setSessionData(null);
    setRecordedBlobs({});
    setInterviewPreset(preset);
    navigate('/interview');
  };

  const renderSection = () => {
    if (activeSection === 'history') return <HistoryPage />;
    if (activeSection === 'profile') {
      return (
        <div className="empty-page">
          <div className="eyebrow">Account</div>
          <h1 className="page-title">Hồ sơ cá nhân</h1>
          <p className="page-subtitle">Thông tin dùng cho các phiên luyện tập của bạn.</p>
          <div className="profile-card">
            <div className="profile-avatar">ND</div>
            <div>
              <div className="history-role">{user?.full_name || user?.name || 'Ứng viên'}</div>
              <div className="history-date">{user?.email} · Thành viên từ tháng 10/2026</div>
            </div>
          </div>
          <button 
            className="secondary-button" 
            style={{ marginTop: 20, color: '#ef4444', borderColor: '#fca5a5' }} 
            onClick={handleLogout}
          >
            Đăng xuất tài khoản
          </button>
        </div>
      );
    }
    if (activeSection === 'home') {
      return (
        <UserHomePage
          user={user}
          onStartInterview={handleStartFromHome}
          onOpenHistory={() => handleNavigation('history')}
        />
      );
    }

    const querySessionId = typeof window !== 'undefined' ? new URLSearchParams(window.location.search).get('session_id') : null;
    const activeSessionId = sessionData?.session_id || querySessionId || (typeof localStorage !== 'undefined' ? localStorage.getItem('interviewlab_last_session_id') : null);

    if (currentPage === 'setup') {
      return (
        <SetupPage 
          initialPositionId={interviewPreset?.positionId} 
          initialLevel={interviewPreset?.level} 
          onStartInterview={handleStartInterview} 
        />
      );
    }
    if (currentPage === 'interview' && sessionData) {
      return (
        <InterviewRoom 
          session={sessionData} 
          stream={cameraStream} 
          onFinishInterview={handleFinishInterview} 
        />
      );
    }
    if (currentPage === 'dashboard' && activeSessionId) {
      return (
        <DashboardPage 
          sessionId={activeSessionId} 
          blobsMap={recordedBlobs} 
          onRestart={handleRestart} 
        />
      );
    }
    return (
      <SetupPage 
        initialPositionId={interviewPreset?.positionId} 
        initialLevel={interviewPreset?.level} 
        onStartInterview={handleStartInterview} 
      />
    );
  };

  const navItems = [
    ['home', 'Trang chủ', Home],
    ['interview', 'Phỏng vấn', Video],
    ['history', 'Lịch sử', History],
    ['profile', 'Hồ sơ', UserRound],
  ];

  if (route.startsWith('/admin')) {
    return (
      <AdminLayout currentRoute={route} onNavigate={(path) => { window.history.pushState({}, '', path); setRoute(path); }} />
    );
  }

  if (!user) {
    if (route === '/' || route === '/home') {
      return (
        <>
          <header className="app-header public-header">
            <div className="brand"><span className="brand-mark"><Mic2 size={18} /></span><span>InterviewLab</span></div>
            <div className="public-actions">
              <button className="auth-link" onClick={() => { setPublicPage('login'); navigate('/login'); }}>Đăng nhập</button>
              <button className="primary-button" onClick={() => { setPublicPage('register'); navigate('/register'); }}>Đăng ký</button>
            </div>
          </header>
          <HomePage onLogin={() => { setPublicPage('login'); navigate('/login'); }} onRegister={() => { setPublicPage('register'); navigate('/register'); }} />
        </>
      );
    }
    return (
      <>
        <header className="app-header public-header">
          <div className="brand"><span className="brand-mark"><Mic2 size={18} /></span><span>InterviewLab</span></div>
          <button className="auth-link" onClick={() => { setPublicPage('home'); navigate('/'); }}>Trang chủ</button>
        </header>
        <AuthPage 
          mode={route === '/register' ? 'register' : 'login'} 
          onModeChange={(mode) => { setPublicPage(mode); navigate(`/${mode}`); }} 
          onAuthenticated={(nextUser) => { 
            setUser(nextUser); 
            try {
              localStorage.setItem('interviewlab_user', JSON.stringify(nextUser));
            } catch (e) {}
            if (nextUser?.email === 'admin@mockinterview.ai' || nextUser?.email === 'admin@interviewlab.test' || nextUser?.role === 'admin' || nextUser?.role === 'ADMIN') {
              navigate('/admin');
            } else {
              setActiveSection('home'); 
              setCurrentPage('setup'); 
              navigate('/home'); 
            }
          }} 
        />
      </>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <a href="/" className="brand" onClick={(e) => { e.preventDefault(); handleNavigation('home'); }}>
          <span className="brand-mark"><Mic2 size={18} /></span>
          <span>InterviewLab</span>
        </a>
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
          <button className="sidebar-item sidebar-logout" onClick={handleLogout}>
            <LogOut size={17} /><span>Đăng xuất</span>
          </button>
          <div className="sidebar-note">
            <Sparkles size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} /> AI phân tích giúp bạn cải thiện từng câu trả lời.
          </div>
        </aside>
        <main className="main-content">{renderSection()}</main>
      </div>
    </div>
  );
}
