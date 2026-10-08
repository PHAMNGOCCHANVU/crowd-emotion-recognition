import React, { useState, useEffect, useRef } from 'react';
import ScoreCard from '../components/ScoreCard';
import VideoPreview from '../components/VideoPreview';
import EmotionChart from '../components/EmotionChart';
import FeedbackAccordion from '../components/FeedbackAccordion';
import { api } from '../services/api';

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
    <div style={{ maxWidth: '1100px', margin: '30px auto', padding: '0 20px' }}>
      {/* Tiêu đề & Nút làm lại */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ margin: '0 0 6px', fontSize: '26px', color: '#f8fafc', fontWeight: 800 }}>
            📊 Báo cáo Đánh giá Phỏng vấn Đa phương thức
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#94a3b8' }}>
            Kết quả tổng hợp từ Mô hình Cảm xúc (FER) + Whisper STT + Trí tuệ Nhân tạo Gemini
          </p>
        </div>
        <button
          onClick={onRestart}
          style={{
            padding: '10px 20px',
            borderRadius: '8px',
            border: '1px solid #475569',
            background: '#1e293b',
            color: '#f8fafc',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          🔄 Luyện tập phiên mới
        </button>
      </div>

      {/* Thẻ điểm tổng quan */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '28px' }}>
        <ScoreCard title="Điểm Tổng Hợp" score={summary.overall_score} color="#3b82f6" subtitle="60% Chuyên môn + 40% Phong thái" />
        <ScoreCard title="Năng Lực Chuyên Môn" score={summary.content_score_avg} color="#10b981" subtitle="Đánh giá theo phương pháp STAR" />
        <ScoreCard title="Chỉ Số Tự Tin (FER)" score={summary.confidence_score_avg} color="#38bdf8" subtitle="Tỷ lệ nét mặt tươi tắn & điềm đạm" />
        <ScoreCard title="Mức Độ Căng Thẳng" score={summary.stress_score_avg} color="#f59e0b" subtitle="Nét mặt bối rối / nhăn nhó" />
        <ScoreCard title="Từ Đệm Ngập Ngừng" score={summary.total_filler_words} isCount color="#e2e8f0" subtitle="'ừm', 'à', 'uhm' trong bài nói" />
      </div>

      {/* Khu vực phát lại video đồng bộ với biểu đồ timeline */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', color: '#f1f5f9' }}>
              🎥 Xem lại Video Câu {currentOrder} (Client-side Blob)
            </h3>
            {/* Chọn câu để xem lại */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {details.map((d, idx) => (
                <button
                  key={d.order_index}
                  onClick={() => setSelectedQuestionIdx(idx)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: selectedQuestionIdx === idx ? '#3b82f6' : '#334155',
                    color: '#fff',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Câu {d.order_index}
                </button>
              ))}
            </div>
          </div>

          <VideoPreview
            videoBlobUrl={currentBlobUrl}
            videoRef={videoPlayerRef}
            onTimeUpdate={(t) => setVideoCurrentTime(t)}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <EmotionChart
            timeline={currentDetail.emotion_timeline || []}
            onSeekSecond={handleSeekSecond}
            currentSecond={videoCurrentTime}
          />

          <div style={{ background: '#1e293b', padding: '16px', borderRadius: '12px', border: '1px solid #334155' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8', marginBottom: '6px' }}>
              💡 Lời khuyên Phong thái cho Câu {currentOrder}:
            </div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              {currentDetail.ai_feedback?.delivery_critique || 'Đang cập nhật...'}
            </div>
          </div>
        </div>
      </div>

      {/* Chi tiết từng câu hỏi & Nhận xét của AI */}
      <div style={{ marginBottom: '40px' }}>
        <h3 style={{ fontSize: '18px', color: '#f8fafc', marginBottom: '16px' }}>
          📝 Chi tiết Đánh giá Từng Câu hỏi
        </h3>
        <FeedbackAccordion
          details={details}
          activeIndex={selectedQuestionIdx}
          onSelectQuestion={(idx) => setSelectedQuestionIdx(idx)}
        />
      </div>
    </div>
  );
}
