import React, { useState } from 'react';

export default function FeedbackAccordion({ details = [], activeIndex = 0, onSelectQuestion }) {
  const [selected, setSelected] = useState(activeIndex);

  const handleSelect = (idx) => {
    setSelected(idx);
    if (onSelectQuestion) onSelectQuestion(idx);
  };

  if (!details || details.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {details.map((item, idx) => {
        const isOpen = selected === idx;
        const feedback = item.ai_feedback || {};

        return (
          <div
            key={item.order_index}
            style={{
              background: '#1e293b',
              borderRadius: '12px',
              border: isOpen ? '1px solid #3b82f6' : '1px solid #334155',
              overflow: 'hidden',
              transition: 'border-color 0.2s',
            }}
          >
            {/* Header Accordion */}
            <div
              onClick={() => handleSelect(idx)}
              style={{
                padding: '16px 20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: 'pointer',
                background: isOpen ? '#1e293b' : '#0f172a',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{
                  background: isOpen ? '#3b82f6' : '#334155',
                  color: '#fff',
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: 600,
                }}>
                  {item.order_index}
                </span>
                <span style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
                  {item.question_text}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{ fontSize: '13px', color: '#38bdf8' }}>
                  Điểm: {item.metrics?.content_score || 80}/100
                </span>
                <span style={{ color: '#94a3b8', fontSize: '18px' }}>
                  {isOpen ? '▲' : '▼'}
                </span>
              </div>
            </div>

            {/* Content Body */}
            {isOpen && (
              <div style={{ padding: '20px', borderTop: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Transcript */}
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px', fontWeight: 600 }}>
                    🎙️ BẢN BÓC BĂNG CÂU TRẢ LỜI (WHISPER STT)
                  </div>
                  <div style={{ background: '#0f172a', padding: '12px 16px', borderRadius: '8px', fontSize: '14px', lineHeight: 1.6, color: '#cbd5e1' }}>
                    "{item.transcript || 'Chưa có bản bóc băng'}"
                  </div>
                  {item.filler_words_count > 0 && (
                    <div style={{ fontSize: '12px', color: '#f59e0b', marginTop: '6px' }}>
                      ⚠️ Phát hiện {item.filler_words_count} từ ngập ngừng ("ừm", "à").
                    </div>
                  )}
                </div>

                {/* Nhận xét chuyên môn & Phong thái */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #3b82f6' }}>
                    <div style={{ fontSize: '12px', color: '#60a5fa', fontWeight: 600, marginBottom: '6px' }}>
                      🧠 ĐÁNH GIÁ CHUYÊN MÔN (STAR)
                    </div>
                    <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>
                      {feedback.content_critique || 'Đang cập nhật...'}
                    </div>
                  </div>

                  <div style={{ background: '#0f172a', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #22c55e' }}>
                    <div style={{ fontSize: '12px', color: '#4ade80', fontWeight: 600, marginBottom: '6px' }}>
                      👁️ ĐÁNH GIÁ PHONG THÁI & BIỂU CẢM (FER)
                    </div>
                    <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>
                      {feedback.delivery_critique || 'Đang cập nhật...'}
                    </div>
                  </div>
                </div>

                {/* Gợi ý câu trả lời mẫu */}
                {feedback.suggested_answer && (
                  <div style={{ background: '#14291f', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #10b981' }}>
                    <div style={{ fontSize: '12px', color: '#34d399', fontWeight: 600, marginBottom: '6px' }}>
                      💡 GỢI Ý CÂU TRẢ LỜI MẪU TỐI ƯU
                    </div>
                    <div style={{ fontSize: '13px', color: '#d1fae5', lineHeight: 1.5 }}>
                      {feedback.suggested_answer}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
