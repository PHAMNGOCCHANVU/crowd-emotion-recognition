import React, { useState } from 'react';

export default function FeedbackAccordion({ details = [], activeIndex = 0, onSelectQuestion }) {
  const [selected, setSelected] = useState(activeIndex);

  const handleSelect = (idx) => {
    setSelected(idx);
    if (onSelectQuestion) onSelectQuestion(idx);
  };

  if (!details || details.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {details.map((item, idx) => {
        const isOpen = selected === idx;
        const feedback = item.ai_feedback || {};

        return (
          <div
            key={item.order_index}
            style={{
              background: '#fff',
              borderRadius: '12px',
              border: isOpen ? '1px solid #7da9d6' : '1px solid #e5eaf1',
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
                background: isOpen ? '#f8fbff' : '#fff',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{
                  background: isOpen ? '#1e5b9e' : '#dbe4ef',
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
                <span style={{ fontSize: '15px', fontWeight: 650, color: '#1b2b43' }}>
                  {item.question_text}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{ fontSize: '13px', color: '#356ca8', fontWeight: 700 }}>
                Điểm: {item.metrics?.content_score ?? '—'}/100
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
                  <div style={{ background: '#f5f7fa', padding: '12px 16px', borderRadius: '8px', fontSize: '14px', lineHeight: 1.6, color: '#46566b' }}>
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
                  <div style={{ background: '#f7fbff', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #4d8bc5' }}>
                    <div style={{ fontSize: '12px', color: '#356ca8', fontWeight: 700, marginBottom: '6px' }}>
                      🧠 ĐÁNH GIÁ CHUYÊN MÔN (STAR)
                    </div>
                    <div style={{ fontSize: '13px', color: '#46566b', lineHeight: 1.5 }}>
                      {feedback.content_critique || 'Đang cập nhật...'}
                    </div>
                  </div>

                  <div style={{ background: '#f5fbf7', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #4b9a6a' }}>
                    <div style={{ fontSize: '12px', color: '#397a55', fontWeight: 700, marginBottom: '6px' }}>
                      👁️ ĐÁNH GIÁ PHONG THÁI & BIỂU CẢM (FER)
                    </div>
                    <div style={{ fontSize: '13px', color: '#46566b', lineHeight: 1.5 }}>
                      {feedback.delivery_critique || 'Đang cập nhật...'}
                    </div>
                  </div>
                </div>

                {/* Gợi ý câu trả lời mẫu */}
                {feedback.suggested_answer && (
                  <div style={{ background: '#f1faf5', padding: '14px', borderRadius: '8px', borderLeft: '3px solid #4b9a6a' }}>
                    <div style={{ fontSize: '12px', color: '#34d399', fontWeight: 600, marginBottom: '6px' }}>
                      💡 GỢI Ý CÂU TRẢ LỜI MẪU TỐI ƯU
                    </div>
                    <div style={{ fontSize: '13px', color: '#356047', lineHeight: 1.5 }}>
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
