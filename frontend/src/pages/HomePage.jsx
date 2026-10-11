import React from 'react';
import { ArrowRight, BarChart3, BrainCircuit, Video } from 'lucide-react';

export default function HomePage({ onLogin, onRegister }) {
  return (
    <div className="public-home">
      <section className="hero">
        <div className="eyebrow">AI-powered interview practice</div>
        <h1>Biến mỗi lần luyện tập thành một bước tiến trong sự nghiệp.</h1>
        <p>Luyện phỏng vấn theo đúng vị trí bạn muốn, ghi hình câu trả lời và nhận báo cáo rõ ràng để cải thiện nhanh hơn.</p>
        <div className="hero-actions">
          <button className="primary-button" onClick={onRegister}>Bắt đầu miễn phí <ArrowRight size={16} /></button>
          <button className="secondary-button" onClick={onLogin}>Đăng nhập</button>
        </div>
      </section>
      <section className="feature-grid">
        {[
          [Video, 'Phỏng vấn mô phỏng', 'Câu hỏi theo vị trí và trải nghiệm phỏng vấn gần với thực tế.'],
          [BrainCircuit, 'Phân tích đa chiều', 'Đánh giá chuyên môn, transcript, cảm xúc và phong thái.'],
          [BarChart3, 'Theo dõi tiến bộ', 'Lưu lịch sử và xem lại kết quả sau mỗi phiên luyện tập.'],
        ].map(([Icon, title, text]) => (
          <div className="feature-card" key={title}><Icon size={21} color="#1e5b9e" /><h3>{title}</h3><p>{text}</p></div>
        ))}
      </section>
    </div>
  );
}
