import React, { useState, useEffect, useRef } from 'react';
import VideoPreview from '../components/VideoPreview';
import { api } from '../services/api';
import { CircleDot, Clock3, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function InterviewRoom({ session, stream, onFinishInterview }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(120);
  const [isRecording, setIsRecording] = useState(false);
  const [blobsMap, setBlobsMap] = useState({}); // { [orderIndex]: blobUrl }

  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);

  const questions = session?.questions || [];
  const currentQuestion = questions[currentIdx] || { order_index: 1, question_text: '' };

  // Khởi động MediaRecorder khi chuyển câu
  useEffect(() => {
    if (!stream) return;

    setTimeLeft(currentQuestion.time_limit_seconds || 120);
    recordedChunksRef.current = [];

    try {
      const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          recordedChunksRef.current.push(e.data);
        }
      };
      recorder.start(1000); // chunk mỗi 1 giây
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      console.warn('MediaRecorder error:', err);
    }

    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, [currentIdx, stream]);

  // Bộ đếm ngược thời gian
  useEffect(() => {
    if (timeLeft <= 0) {
      handleNextQuestion();
      return;
    }
    const timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const handleNextQuestion = () => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.onstop = () => {
        const videoBlob = new Blob(recordedChunksRef.current, { type: 'video/webm' });
        const blobUrl = URL.createObjectURL(videoBlob);

        // 1. Lưu blob URL vào RAM trình duyệt để xem lại không tốn storage server
        const newMap = { ...blobsMap, [currentQuestion.order_index]: blobUrl };
        setBlobsMap(newMap);

        // 2. Gửi ngầm không đợi (In-process Async) lên Backend
        api.uploadAnswer(session.session_id, currentQuestion.order_index, videoBlob).catch((e) => {
          console.warn('Lỗi upload câu:', e);
        });

        // 3. Chuyển sang câu tiếp theo hoặc hoàn thành
        if (currentIdx + 1 < questions.length) {
          setCurrentIdx(currentIdx + 1);
        } else {
          if (onFinishInterview) {
            onFinishInterview(session.session_id, newMap);
          }
        }
      };
      recorder.stop();
    } else {
      if (currentIdx + 1 < questions.length) {
        setCurrentIdx(currentIdx + 1);
      } else {
        if (onFinishInterview) onFinishInterview(session.session_id, blobsMap);
      }
    }
  };

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;

  return (
    <div className="page-shell">
      {/* Thanh tiến độ */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div className="muted" style={{ fontSize: '14px' }}>
          Vị trí: <strong style={{ color: '#1b2b43' }}>{session.role_name}</strong>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {questions.map((q, idx) => (
            <div
              key={q.order_index}
              style={{
                width: '32px',
                height: '8px',
                borderRadius: '4px',
                background: idx === currentIdx ? '#1e5b9e' : idx < currentIdx ? '#4b9a6a' : '#dbe4ef',
              }}
            />
          ))}
        </div>
        <div style={{
          padding: '6px 14px',
          borderRadius: '20px',
          background: timeLeft < 20 ? '#7f1d1d' : '#1e293b',
          color: timeLeft < 20 ? '#fca5a5' : '#f8fafc',
          fontWeight: 700,
          fontSize: '14px',
          border: '1px solid #334155',
        }}>
          <Clock3 size={15} style={{ verticalAlign: 'middle', marginRight: 5 }} />{String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </div>
      </div>

      {/* Khung câu hỏi nổi bật */}
      <div style={{
        background: '#fff',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid #cbdced',
        marginBottom: '24px',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
      }}>
        <div style={{ fontSize: '12px', color: '#356ca8', fontWeight: 800, letterSpacing: '.08em', marginBottom: '8px' }}>
          CÂU HỎI {currentIdx + 1} / {questions.length}
        </div>
        <h2 style={{ margin: 0, fontSize: '20px', color: '#1b2b43', lineHeight: 1.5 }}>
          "{currentQuestion.question_text}"
        </h2>
      </div>

      {/* Khung Camera trực tiếp & Nút nộp */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', alignItems: 'center' }}>
        <div>
          <VideoPreview stream={stream} />
        </div>

        <div className="panel" style={{ padding: '24px', textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '20px' }}>
            <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#ef4444', animation: 'pulse 1.5s infinite' }}></span>
            <span style={{ fontSize: '14px', color: '#1b2b43', fontWeight: 700 }}><CircleDot size={14} color="#c94b4b" style={{ verticalAlign: 'middle', marginRight: 5 }} />Đang ghi hình câu trả lời</span>
          </div>

          <p className="muted" style={{ fontSize: '13px', lineHeight: 1.5, marginBottom: '24px' }}>
            Sau khi trả lời xong, bấm nút bên dưới để chuyển sang câu tiếp theo ngay tức khắc.
          </p>

          <button
            onClick={handleNextQuestion}
            style={{
              width: '100%',
              padding: '16px',
              borderRadius: '10px',
              border: 'none',
              background: '#1e5b9e',
              color: '#fff',
              fontSize: '15px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            {currentIdx + 1 < questions.length ? <><CheckCircle2 size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} />Hoàn thành câu <ArrowRight size={15} style={{ verticalAlign: 'middle', marginLeft: 5 }} /></> : 'Hoàn thành & Xem kết quả'}
          </button>
        </div>
      </div>
    </div>
  );
}
