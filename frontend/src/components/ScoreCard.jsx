import React from 'react';

export default function ScoreCard({ title, score, subtitle, color = '#3b82f6', maxScore = 100, isCount = false }) {
  const percentage = isCount ? null : Math.min(100, Math.max(0, (score / maxScore) * 100));

  return (
    <div className="score-card">
      <div className="score-label">{title}</div>
      <div className="score-value" style={{ color }}>
        {score}{!isCount && <span> /{maxScore}</span>}
      </div>
      {percentage !== null && (
        <div className="score-track">
          <div style={{ width: `${percentage}%`, background: color }} />
        </div>
      )}
      {subtitle && <div className="score-subtitle">{subtitle}</div>}
    </div>
  );
}
