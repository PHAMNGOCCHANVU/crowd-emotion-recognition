import React, { useEffect, useRef } from 'react';

export default function VideoPreview({ stream, videoBlobUrl, onTimeUpdate, videoRef: externalRef }) {
  const localRef = useRef(null);
  const ref = externalRef || localRef;

  useEffect(() => {
    if (ref.current && stream) {
      ref.current.srcObject = stream;
    }
  }, [stream]);

  if (videoBlobUrl) {
    return (
      <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#000' }}>
        <video
          ref={ref}
          src={videoBlobUrl}
          controls
          onTimeUpdate={(e) => onTimeUpdate && onTimeUpdate(e.target.currentTime)}
          style={{ width: '100%', maxHeight: '420px', display: 'block' }}
        />
        <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(0,0,0,0.6)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px' }}>
          📹 Client-Side RAM Replay
        </div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#020617', border: '1px solid #334155' }}>
      <video
        ref={ref}
        autoPlay
        playsInline
        muted
        style={{ width: '100%', maxHeight: '420px', display: 'block', transform: 'scaleX(-1)' }}
      />
      <div style={{ position: 'absolute', bottom: 12, left: 12, display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(15,23,42,0.8)', padding: '6px 12px', borderRadius: '20px', fontSize: '13px' }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
        Webcam Sẵn sàng
      </div>
    </div>
  );
}
