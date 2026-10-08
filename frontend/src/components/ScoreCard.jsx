import React from 'react';

export default function ScoreCard({ title, score, subtitle, color = '#3b82f6', maxScore = 100, isCount = false }) {
  const percentage = isCount ? null : Math.min(100, Math.max(0, (score / maxScore) * 100));

  return (
    <div style={{
      background: '#1e293b',
      padding: '20px',
      borderRadius: '12px',
      border: '1px solid #334155',
      flex: 1,
      minWidth: '180px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    }}>
      <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px', fontWeight: 500 }}>
        {title}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span style={{ fontSize: '32px', fontWeight: 700, color }}>{score}</span>
        {!isCount && <span style={{ fontSize: '14px', color: '#64748b' }}>/{maxScore}</span>}
      </div>
      {percentage !== null && (
        <div style={{ width: '100%', height: '6px', background: '#334155', borderRadius: '3px', marginTop: '12px', overflow: 'hidden' }}>
          <div style={{ width: `${percentage}%`, height: '100%', background: color, borderRadius: '3px', transition: 'width 0.5s ease' }} />
        </div>
      )}
      {subtitle && (
        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '10px' }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}
