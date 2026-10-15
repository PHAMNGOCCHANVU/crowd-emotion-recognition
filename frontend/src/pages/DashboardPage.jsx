import React, { useState, useEffect, useRef } from 'react';
import ScoreCard from '../components/ScoreCard';
import VideoPreview from '../components/VideoPreview';
import EmotionChart from '../components/EmotionChart';
import FeedbackAccordion from '../components/FeedbackAccordion';
import { api } from '../services/api';
import { ArrowLeft, RotateCcw, ShieldCheck, Video, Clock3 } from 'lucide-react';

export default function DashboardPage({ sessionId, blobsMap = {}, onRestart }) {
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState(null);
  const [sessionStatus, setSessionStatus] = useState(null);
  const [selectedQuestionIdx, setSelectedQuestionIdx] = useState(0);
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);

  const videoPlayerRef = useRef(null);

  useEffect(() => {
    let interval = null;

    const checkData = async () => {
      try {
        const [resultsData, statusData] = await Promise.all([
          api.getSessionResults(sessionId).catch(() => null),
          api.getSessionStatus(sessionId).catch(() => null)
        ]);

        if (resultsData) {
          setResults(resultsData);
          setLoading(false);
        }
        if (statusData) {
          setSessionStatus(statusData);
          if (statusData.is_fully_completed && interval) {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.warn('Đang chờ kết quả xử lý từ Backend...', err);
      }
    };

    checkData();
    interval = setInterval(checkData, 3000); // Polling mỗi 3 giây

    return () => clearInterval(interval);
  }, [sessionId]);

  const details = results?.details || [];
  const currentDetail = details[selectedQuestionIdx] || details[0] || {};
  const currentOrder = currentDetail.order_index || 1;
  const currentBlobUrl = blobsMap[currentOrder] || null;
  const currentVideoSrc = currentBlobUrl || currentDetail.video_url || null;

  const questionsStatusList = sessionStatus?.questions || [];
  const completedQuestionsCount = questionsStatusList.filter(q => q.status === 'COMPLETED' || q.status === 'FAILED').length;
  const totalQuestionsCount = questionsStatusList.length || 3;
  const isAnalyzing = sessionStatus ? !sessionStatus.is_fully_completed : (details.length === 0 || details.some(d => !d.ai_feedback || Object.keys(d.ai_feedback).length === 0));

  const handleSeekSecond = (sec) => {
    if (videoPlayerRef.current) {
      videoPlayerRef.current.currentTime = sec;
      setVideoCurrentTime(sec);
    }
  };

  const summary = results?.summary || {
    overall_score: 85.0,
    content_score_avg: 88.0,
    confidence_score_avg: 82.0,
    stress_score_avg: 18.0,
    total_filler_words: 3,
    final_verdict: 'Ứng viên có phản xạ nhanh, phong thái tự tin và biểu cảm tự nhiên.',
  };

  return (
    <div className="page-shell">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap', marginBottom: '16px' }}>
        <div>
          <div className="eyebrow">Interview report</div>
          <h1 className="page-title">Báo cáo phỏng vấn</h1>
          <p className="page-subtitle">Đánh giá tổng hợp về chuyên môn, phong thái và khả năng diễn đạt.</p>
        </div>
        <button className="secondary-button" onClick={onRestart}><RotateCcw size={15} style={{ verticalAlign: 'middle', marginRight: 7 }} />Phiên mới</button>
      </div>

      {/* Banner Trạng Thái Tiến Trình AI */}
      {isAnalyzing && (
        <div style={{
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
        }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            background: '#2563eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '18px',
            flexShrink: 0,
            boxShadow: '0 0 0 4px rgba(37, 99, 235, 0.2)'
          }}>
            🤖
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: '14px', color: '#1e3a8a', marginBottom: '3px' }}>
              AI đang phân tích đa phương thức (FER · Groq Whisper · Gemini)...
            </div>
            <div style={{ fontSize: '12px', color: '#2563eb' }}>
              Tiến độ: Đã hoàn tất {completedQuestionsCount} / {totalQuestionsCount} câu. Kết quả đang được cập nhật tự động...
            </div>
          </div>
          <div style={{ width: '120px', height: '8px', background: '#dbeafe', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${Math.max(10, (completedQuestionsCount / totalQuestionsCount) * 100)}%`,
              background: '#2563eb',
              transition: 'width 0.4s ease'
            }} />
          </div>
        </div>
      )}

      {/* Thẻ điểm tổng quan */}
      <div className="score-grid">
        <ScoreCard title="Điểm Tổng Hợp" score={summary.overall_score} color="#3b82f6" subtitle="60% Chuyên môn + 40% Phong thái" />
        <ScoreCard title="Năng Lực Chuyên Môn" score={summary.content_score_avg} color="#10b981" subtitle="Đánh giá theo phương pháp STAR" />
        <ScoreCard title="Chỉ Số Tự Tin (FER)" score={summary.confidence_score_avg} color="#38bdf8" subtitle="Tỷ lệ nét mặt tươi tắn & điềm đạm" />
        <ScoreCard title="Mức Độ Căng Thẳng" score={summary.stress_score_avg} color="#f59e0b" subtitle="Nét mặt bối rối / nhăn nhó" />
        <ScoreCard title="Từ Đệm Ngập Ngừng" score={summary.total_filler_words} isCount color="#e2e8f0" subtitle="'ừm', 'à', 'uhm' trong bài nói" />
      </div>

      {/* Khu vực phát lại video đồng bộ với biểu đồ timeline */}
      <div className="dashboard-grid">
        <div>
          <div className="panel video-panel">
            <div className="panel-header">
              <h3 className="panel-title"><Video size={16} style={{ verticalAlign: 'middle', marginRight: 8 }} />Video câu {currentOrder}</h3>
              <div className="question-tabs">
            {/* Chọn câu để xem lại */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {details.map((d, idx) => (
                <button
                  key={d.order_index}
                  onClick={() => setSelectedQuestionIdx(idx)}
                  className={`question-tab ${selectedQuestionIdx === idx ? 'active' : ''}`}
                >
                  Câu {d.order_index}
                </button>
              ))}
            </div>
            </div>
          </div>

          <div className="video-area">
            <VideoPreview videoBlobUrl={currentVideoSrc} videoRef={videoPlayerRef} onTimeUpdate={(t) => setVideoCurrentTime(t)} />
          </div>
          </div>

        </div>
        <div>
          <EmotionChart
            timeline={currentDetail.emotion_timeline || []}
            onSeekSecond={handleSeekSecond}
            currentSecond={videoCurrentTime}
          />

          <div className="insight-box">
            <div className="insight-label">Gợi ý phong thái · Câu {currentOrder}</div>
            <div className="insight-text">
              {currentDetail.ai_feedback?.delivery_critique || 'Đang cập nhật...'}
            </div>
          </div>
        </div>
      </div>

      {/* Chi tiết từng câu hỏi & Nhận xét của AI */}
      <div style={{ marginBottom: '40px' }}>
        <h3 className="section-heading"><ShieldCheck size={18} style={{ verticalAlign: 'middle', marginRight: 8 }} />Chi tiết đánh giá từng câu hỏi</h3>
        <FeedbackAccordion
          details={details}
          activeIndex={selectedQuestionIdx}
          onSelectQuestion={(idx) => setSelectedQuestionIdx(idx)}
        />
      </div>
    </div>
  );
}
