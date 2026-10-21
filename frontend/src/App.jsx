import React, { useEffect, useState } from 'react';
import SetupPage from './pages/SetupPage';
import InterviewRoom from './pages/InterviewRoom';
import DashboardPage from './pages/DashboardPage';
import HomePage from './pages/HomePage';
import AuthPage from './pages/AuthPage';
import UserHomePage from './pages/UserHomePage';
import HistoryPage from './pages/HistoryPage';
import PracticePage from './pages/PracticePage';
import ProfilePage from './pages/ProfilePage';
import ChatbotDrawer from './components/ChatbotDrawer';
import {
  Mic2,
  Home,
  BookOpen,
  Video,
  History,
  UserRound,
  Sparkles,
  LogOut,
} from 'lucide-react';
import AdminLayout from './pages/Admin/AdminLayout';

export default function App() {
  const initialPath = window.location.pathname;
  const [route, setRoute] = useState(initialPath);
  const [currentPage, setCurrentPage] = useState(
    initialPath.startsWith('/results') ? 'dashboard' : 'setup'
  ); // 'setup' | 'interview' | 'dashboard'

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
  const [activeSection, setActiveSection] = useState(() => {
    if (initialPath === '/practice') return 'practice';
    if (initialPath === '/history') return 'history';
    if (initialPath === '/profile') return 'profile';
    if (initialPath === '/interview' || initialPath.startsWith('/results')) return 'interview';
    return 'home';
  });
  const [interviewPreset, setInterviewPreset] = useState(null);
  const [, setPublicPage] = useState(
    initialPath === '/register' ? 'register' : initialPath === '/login' ? 'login' : 'home'
  );

  // State điều khiển Global Chatbot Slide-over Drawer
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      setRoute(path);
      if (path.startsWith('/results')) {
        setCurrentPage('dashboard');
        setActiveSection('interview');
      } else if (path === '/practice') {
        setActiveSection('practice');
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
    setIsChatOpen(false);
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

  const handleViewSessionDetail = (sessionId) => {
    navigate(`/results?session_id=${sessionId}`);
    setCurrentPage('dashboard');
    setActiveSection('interview');
  };

  const isInterviewing = currentPage === 'interview' && Boolean(sessionData);

  const renderSection = () => {
    if (activeSection === 'practice') {
      return (
        <PracticePage
          onStartInterview={handleStartFromHome}
        />
      );
    }
    if (activeSection === 'history') {
      return <HistoryPage onViewSessionDetail={handleViewSessionDetail} />;
    }
    if (activeSection === 'profile') {
      return (
        <ProfilePage
          user={user}
          onUserUpdated={(updated) => {
            setUser(updated);
            try {
              localStorage.setItem('interviewlab_user', JSON.stringify(updated));
            } catch (e) {}
          }}
          onLogout={handleLogout}
        />
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

    const querySessionId =
      typeof window !== 'undefined'
        ? new URLSearchParams(window.location.search).get('session_id')
        : null;
    const activeSessionId =
      sessionData?.session_id ||
      querySessionId ||
      (typeof localStorage !== 'undefined'
        ? localStorage.getItem('interviewlab_last_session_id')
        : null);

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
    ['practice', 'Ôn luyện', BookOpen],
    ['interview', 'Phỏng vấn', Video],
    ['history', 'Lịch sử', History],
    ['profile', 'Hồ sơ', UserRound],
  ];

  if (route.startsWith('/admin')) {
    return (
      <AdminLayout
        currentRoute={route}
        onNavigate={(path) => {
          window.history.pushState({}, '', path);
          setRoute(path);
        }}
      />
    );
  }

  if (!user) {
    if (route === '/' || route === '/home') {
      return (
        <>
          <header className="app-header public-header">
            <div className="brand">
              <span className="brand-mark"><Mic2 size={18} /></span>
              <span>InterviewLab</span>
            </div>
            <div className="public-actions">
              <button
                className="auth-link"
                onClick={() => {
                  setPublicPage('login');
                  navigate('/login');
                }}
              >
                Đăng nhập
              </button>
              <button
                className="primary-button"
                onClick={() => {
                  setPublicPage('register');
                  navigate('/register');
                }}
              >
                Đăng ký
              </button>
            </div>
          </header>
          <HomePage
            onLogin={() => {
              setPublicPage('login');
              navigate('/login');
            }}
            onRegister={() => {
              setPublicPage('register');
              navigate('/register');
            }}
          />
        </>
      );
    }
    return (
      <>
        <header className="app-header public-header">
          <div className="brand">
            <span className="brand-mark"><Mic2 size={18} /></span>
            <span>InterviewLab</span>
          </div>
          <button
            className="auth-link"
            onClick={() => {
              setPublicPage('home');
              navigate('/');
            }}
          >
            Trang chủ
          </button>
        </header>
        <AuthPage
          mode={route === '/register' ? 'register' : 'login'}
          onModeChange={(mode) => {
            setPublicPage(mode);
            navigate(`/${mode}`);
          }}
          onAuthenticated={(nextUser) => {
            setUser(nextUser);
            try {
              localStorage.setItem('interviewlab_user', JSON.stringify(nextUser));
            } catch (e) {}
            if (
              nextUser?.email === 'admin@mockinterview.ai' ||
              nextUser?.email === 'admin@interviewlab.test' ||
              nextUser?.role === 'admin' ||
              nextUser?.role === 'ADMIN'
            ) {
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
      {/* Global Header */}
      <header className="app-header">
        <a
          href="/"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            handleNavigation('home');
          }}
        >
          <span className="brand-mark"><Mic2 size={18} /></span>
          <span>InterviewLab</span>
        </a>

        {/* Cụm Action Header: Nút Trigger mở AI Cố vấn */}
        <div className="header-actions">
          {!isInterviewing && (
            <button
              className="advisor-trigger-btn"
              onClick={() => setIsChatOpen(true)}
              title="Mở AI Cố vấn phỏng vấn"
            >
              <Sparkles size={16} />
              <span>AI Cố vấn</span>
            </button>
          )}
        </div>
      </header>

      <div className="app-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <p className="sidebar-label">Workspace</p>
          <nav className="sidebar-nav">
            {navItems.map(([id, label, Icon]) => (
              <button
                key={id}
                className={`sidebar-item ${activeSection === id ? 'active' : ''}`}
                onClick={() => handleNavigation(id)}
              >
                <Icon size={17} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
          <button className="sidebar-item sidebar-logout" onClick={handleLogout}>
            <LogOut size={17} />
            <span>Đăng xuất</span>
          </button>
        </aside>

        {/* Main Content */}
        <main className="main-content">{renderSection()}</main>
      </div>

      {/* Global Slide-over Chatbot Drawer */}
      <ChatbotDrawer
        isOpen={isChatOpen && !isInterviewing}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}
