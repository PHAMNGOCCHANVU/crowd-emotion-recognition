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
  const [selectedQuestionIdx, setSelectedQuestionIdx] = useState(0);
  const [videoCurrentTime, setVideoCurrentTime] = useState(0);

  const videoPlayerRef = useRef(null);

  useEffect(() => {
    let interval = null;

    const fetchResults = async () => {
      try {
        const data = await api.getSessionResults(sessionId);
        setResults(data);
        setLoading(false);
      } catch (err) {
        console.warn('Đang chờ kết quả xử lý từ Backend...', err);
      }
    };

    fetchResults();
    interval = setInterval(fetchResults, 3000); // Polling mỗi 3 giây

    return () => clearInterval(interval);
  }, [sessionId]);

  const details = results?.details || [];
  const currentDetail = details[selectedQuestionIdx] || details[0] || {};
  const currentOrder = currentDetail.order_index || 1;
  const currentBlobUrl = blobsMap[currentOrder] || null;

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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
        <div>
          <div className="eyebrow">Interview report</div>
          <h1 className="page-title">Báo cáo phỏng vấn</h1>
          <p className="page-subtitle">Đánh giá tổng hợp về chuyên môn, phong thái và khả năng diễn đạt.</p>
        </div>
        <button className="secondary-button" onClick={onRestart}><RotateCcw size={15} style={{ verticalAlign: 'middle', marginRight: 7 }} />Phiên mới</button>
      </div>

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
            <VideoPreview videoBlobUrl={currentBlobUrl} videoRef={videoPlayerRef} onTimeUpdate={(t) => setVideoCurrentTime(t)} />
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
