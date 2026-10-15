import React from 'react';

const EMOTION_COLORS = {
  Happy: '#22c55e',     // Xanh lá (Tự tin/Tích cực)
  Normal: '#3b82f6',    // Xanh dương (Điềm đạm/Bình thản)
  Sad: '#ef4444',       // Đỏ (Buồn bã/Căng thẳng)
  Surprised: '#f59e0b', // Vàng cam (Hoang mang/Bối rối)
  Fear: '#8b5cf6',      // Tím (Lo âu/Áp lực)
  Contempt: '#ec4899',  // Hồng đậm (Khó chịu/Coi thường)
};


export default function EmotionChart({ timeline = [], onSeekSecond, currentSecond = 0 }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="panel" style={{ padding: '24px', textAlign: 'center', color: '#718096' }}>
        Chưa có dữ liệu cảm xúc dòng thời gian.
      </div>
    );
  }

  return (
    <div className="panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 className="panel-title">
          Diễn biến cảm xúc theo thời gian
        </h4>
        <div style={{ display: 'flex', gap: '14px', fontSize: '12px' }}>
          {Object.entries(EMOTION_COLORS).map(([emo, color]) => (
            <div key={emo} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: 10, height: 10, borderRadius: '2px', background: color }}></span>
              <span style={{ color: '#718096' }}>{emo}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Thanh biểu đồ khối trực quan theo từng giây */}
      <div style={{ display: 'flex', gap: '3px', alignItems: 'flex-end', height: '80px', padding: '8px 0', borderBottom: '1px solid #475569' }}>
        {timeline.map((item) => {
          const isCurrent = Math.floor(currentSecond) === item.second;
          const color = EMOTION_COLORS[item.emotion] || '#94a3b8';
          const height = `${Math.max(25, (item.confidence || 0.8) * 100)}%`;

          return (
            <div
              key={item.second}
              onClick={() => onSeekSecond && onSeekSecond(item.second)}
              title={`Giây ${item.second}: ${item.emotion} (${Math.round((item.confidence || 0.8) * 100)}%)`}
              style={{
                flex: 1,
                height,
                background: color,
                borderRadius: '3px',
                cursor: 'pointer',
                opacity: isCurrent ? 1 : 0.85,
                border: isCurrent ? '2px solid #fff' : 'none',
                transition: 'all 0.15s ease',
              }}
            />
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
        <span>0s</span>
        <span>{timeline[timeline.length - 1]?.second || 0}s</span>
      </div>
    </div>
  );
}
