import React, { useState } from 'react';
import { Plus, Edit3, Trash2 } from 'lucide-react';

const initialJobs = [
  { id: 1, title: 'Software Engineer', questions: 5, status: 'Active' },
  { id: 2, title: 'Data Analyst', questions: 4, status: 'Active' },
  { id: 3, title: 'Sales / Business Development', questions: 3, status: 'Active' },
  { id: 4, title: 'Marketing', questions: 4, status: 'Draft' },
  { id: 5, title: 'Human Resources (HR)', questions: 3, status: 'Draft' },
];

export default function AdminInterviews() {
  const [jobs, setJobs] = useState(initialJobs);

  const handleAddJob = () => {
    alert("Thêm Vị trí mới sẽ mở form thêm dữ liệu lên Backend");
  };

  const handleEditJob = (title) => {
    alert(`Mở popup chỉnh sửa thông tin cho vị trí: ${title}`);
  };

  const handleDeleteJob = (id, title) => {
    if (window.confirm(`Bạn có chắc muốn xóa vị trí: ${title}?`)) {
      setJobs(jobs.filter(job => job.id !== id));
    }
  };

  const handleManageJD = (title) => {
    alert(`Chuyển hướng đến trang chỉnh sửa JD và Bộ câu hỏi AI cho: ${title}`);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0 }}>Bộ Câu hỏi & Vị trí</h1>
        <button 
          onClick={handleAddJob}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#3b82f6', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', transition: 'background 0.2s' }}
        >
          <Plus size={18} /> Thêm Vị trí mới
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
        {jobs.length > 0 ? jobs.map(job => (
          <div key={job.id} className="panel" style={{ padding: '24px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: 24, right: 24, display: 'flex', gap: '8px' }}>
              <button onClick={() => handleEditJob(job.title)} style={{ background: '#f1f5f9', border: 'none', padding: '6px', borderRadius: '6px', color: '#64748b', cursor: 'pointer' }}>
                <Edit3 size={16} />
              </button>
              <button onClick={() => handleDeleteJob(job.id, job.title)} style={{ background: '#fef2f2', border: 'none', padding: '6px', borderRadius: '6px', color: '#ef4444', cursor: 'pointer' }}>
                <Trash2 size={16} />
              </button>
            </div>
            
            <div style={{ display: 'inline-block', padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, marginBottom: '16px', 
              background: job.status === 'Active' ? '#dcfce7' : '#f1f5f9', 
              color: job.status === 'Active' ? '#166534' : '#475569' 
            }}>
              {job.status === 'Active' ? 'Đang hoạt động' : 'Bản nháp'}
            </div>
            
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>{job.title}</h3>
            <p style={{ color: '#64748b', fontSize: '14px', margin: '0 0 20px 0' }}>Bao gồm {job.questions} câu hỏi AI sinh sẵn.</p>
            
            <button 
              onClick={() => handleManageJD(job.title)}
              style={{ width: '100%', padding: '10px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', color: '#3b82f6', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s' }}
              onMouseOver={(e) => { e.target.style.background = '#eff6ff'; e.target.style.borderColor = '#bfdbfe'; }}
              onMouseOut={(e) => { e.target.style.background = '#f8fafc'; e.target.style.borderColor = '#e2e8f0'; }}
            >
              Quản lý JD & Câu hỏi
            </button>
          </div>
        )) : (
          <div style={{ gridColumn: 'span 3', textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
            Chưa có vị trí nào. Hãy thêm mới!
          </div>
        )}
      </div>
    </div>
  );
}