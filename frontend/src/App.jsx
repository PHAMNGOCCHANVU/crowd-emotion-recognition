import React, { useState } from 'react';
import SetupPage from './pages/SetupPage';
import InterviewRoom from './pages/InterviewRoom';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  const [currentPage, setCurrentPage] = useState('setup'); // 'setup' | 'interview' | 'dashboard'
  const [sessionData, setSessionData] = useState(null);
  const [cameraStream, setCameraStream] = useState(null);
  const [recordedBlobs, setRecordedBlobs] = useState({});

  const handleStartInterview = (session, stream) => {
    setSessionData(session);
    setCameraStream(stream);
    setCurrentPage('interview');
  };

  const handleFinishInterview = (sessionId, blobsMap) => {
    setRecordedBlobs(blobsMap);
    // Tắt camera khi đã phỏng vấn xong
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
    setCurrentPage('dashboard');
  };

  const handleRestart = () => {
    setSessionData(null);
    setRecordedBlobs({});
    setCurrentPage('setup');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#f8fafc', paddingBottom: '40px' }}>
      {/* Thanh điều hướng tối giản */}
      <header style={{
        background: '#1e293b',
        borderBottom: '1px solid #334155',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '18px', fontWeight: 700 }}>
          <span>🎙️</span>
          <span>AI Mock Interview Platform</span>
        </div>
        <div style={{ fontSize: '13px', color: '#94a3b8' }}>
          Đa phương thức: FER (ResNet-18) + Whisper STT + Gemini Flash
        </div>
      </header>

      {/* Nội dung trang tương ứng */}
      <main>
        {currentPage === 'setup' && (
          <SetupPage onStartInterview={handleStartInterview} />
        )}

        {currentPage === 'interview' && sessionData && (
          <InterviewRoom
            session={sessionData}
            stream={cameraStream}
            onFinishInterview={handleFinishInterview}
          />
        )}

        {currentPage === 'dashboard' && sessionData && (
          <DashboardPage
            sessionId={sessionData.session_id}
            blobsMap={recordedBlobs}
            onRestart={handleRestart}
          />
        )}
      </main>
    </div>
  );
}
