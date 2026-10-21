import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  HelpCircle,
  Layers,
  FolderTree,
  Plus,
  Edit,
  Trash2,
  X,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { api } from '../../services/api';

export default function AdminInterviews() {
  const [activeTab, setActiveTab] = useState('positions'); // positions | questions | industries | segments
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Data states
  const [positions, setPositions] = useState([]);
  const [industries, setIndustries] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [segments, setSegments] = useState([]);

  // Question Filters
  const [filterPositionId, setFilterPositionId] = useState('');
  const [filterLevel, setFilterLevel] = useState('');

  // Modals
  const [modalType, setModalType] = useState(null); // 'create_position' | 'edit_position' | 'create_question' | 'edit_question' | 'create_industry' | 'edit_industry' | 'create_segment' | 'edit_segment'
  const [editingItem, setEditingItem] = useState(null);

  // Form states
  const [formData, setFormData] = useState({});

  const showNotification = (msg, isError = false) => {
    if (isError) {
      setError(msg);
      setTimeout(() => setError(null), 4000);
    } else {
      setSuccessMsg(msg);
      setTimeout(() => setSuccessMsg(null), 3000);
    }
  };

  // Load initial data
  const loadData = async () => {
    setLoading(true);
    try {
      const [posData, indData] = await Promise.all([
        api.adminGetPositions(),
        api.adminGetIndustries(),
      ]);
      setPositions(posData);
      setIndustries(indData);
      if (posData.length > 0 && !filterPositionId) {
        setFilterPositionId(posData[0].id);
      }
    } catch (err) {
      console.error('Lỗi nạp dữ liệu Admin:', err);
      showNotification('Không thể nạp dữ liệu ban đầu.', true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Load questions when filter changes or on questions tab
  const loadQuestions = async () => {
    if (!filterPositionId) return;
    setLoading(true);
    try {
      const res = await api.getQuestions({
        positionId: filterPositionId,
        level: filterLevel || undefined,
      });
      setQuestions(res.questions || []);
    } catch (err) {
      console.error('Lỗi nạp câu hỏi:', err);
      setQuestions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'questions' && filterPositionId) {
      loadQuestions();
    }
  }, [activeTab, filterPositionId, filterLevel]);

  // Load segments when on segments tab
  const loadSegments = async () => {
    setLoading(true);
    try {
      const data = await api.getSegments();
      setSegments(data);
    } catch (err) {
      console.error('Lỗi nạp phân khúc:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'segments') {
      loadSegments();
    }
  }, [activeTab]);

  // ----------------------------------------------------------------------
  // HANDLERS: POSITIONS
  // ----------------------------------------------------------------------
  const handleOpenPositionModal = (pos = null) => {
    if (pos) {
      setEditingItem(pos);
      setFormData({
        name: pos.name,
        code: pos.code || '',
        industry_id: pos.industry_id || (industries[0]?.id || ''),
        skills: Array.isArray(pos.skills) ? pos.skills.join(', ') : '',
        duration: pos.duration || '3–6 tháng',
        icon: pos.icon || 'server',
      });
      setModalType('edit_position');
    } else {
      setEditingItem(null);
      setFormData({
        name: '',
        code: '',
        industry_id: industries[0]?.id || '',
        skills: 'Python, SQL',
        duration: '3–6 tháng',
        icon: 'server',
      });
      setModalType('create_position');
    }
  };

  const handleSavePosition = async (e) => {
    e.preventDefault();
    const skillsArray = (formData.skills || '')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      if (editingItem) {
        await api.adminUpdatePosition(editingItem.id, {
          name: formData.name,
          code: formData.code,
          industry_id: formData.industry_id,
          skills: skillsArray,
          duration: formData.duration,
          icon: formData.icon,
        });
        showNotification('Cập nhật vị trí thành công!');
      } else {
        await api.adminCreatePosition({
          name: formData.name,
          code: formData.code || formData.name.toLowerCase().replace(/\s+/g, '-'),
          industry_id: formData.industry_id,
          skills: skillsArray,
          duration: formData.duration,
          icon: formData.icon,
        });
        showNotification('Thêm vị trí mới thành công!');
      }
      setModalType(null);
      const updatedPositions = await api.adminGetPositions();
      setPositions(updatedPositions);
    } catch (err) {
      console.error('Lỗi lưu vị trí:', err);
      showNotification(err.response?.data?.detail || 'Thao tác vị trí thất bại.', true);
    }
  };

  const handleDeletePosition = async (pos) => {
    if (!window.confirm(`Bạn có chắc muốn xóa vị trí "${pos.name}"?`)) return;
    try {
      await api.adminDeletePosition(pos.id);
      showNotification('Đã xóa vị trí thành công!');
      const updated = await api.adminGetPositions();
      setPositions(updated);
    } catch (err) {
      console.error('Lỗi xóa vị trí:', err);
      showNotification(err.response?.data?.detail || 'Không thể xóa vị trí (vướng ràng buộc dữ liệu).', true);
    }
  };

  // ----------------------------------------------------------------------
  // HANDLERS: QUESTIONS
  // ----------------------------------------------------------------------
  const handleOpenQuestionModal = (q = null) => {
    if (q) {
      setEditingItem(q);
      setFormData({
        category: q.category || 'Chuyên môn',
        question_text: q.question_text || '',
        time_limit_seconds: q.time_limit_seconds || 120,
        level: q.level || 'junior',
        levels: Array.isArray(q.levels) ? q.levels.join(', ') : (q.level || 'junior'),
      });
      setModalType('edit_question');
    } else {
      setEditingItem(null);
      setFormData({
        position_id: filterPositionId,
        category: 'Chuyên môn',
        question_text: '',
        time_limit_seconds: 120,
        level: filterLevel || 'junior',
        levels: filterLevel || 'junior',
      });
      setModalType('create_question');
    }
  };

  const handleSaveQuestion = async (e) => {
    e.preventDefault();
    const levelsArray = (formData.levels || '')
      .split(',')
      .map((l) => l.trim().toLowerCase())
      .filter(Boolean);

    try {
      if (editingItem) {
        await api.adminUpdateQuestion(editingItem.id, {
          category: formData.category,
          question_text: formData.question_text,
          time_limit_seconds: Number(formData.time_limit_seconds),
          level: formData.level,
          levels: levelsArray.length > 0 ? levelsArray : [formData.level],
        });
        showNotification('Cập nhật câu hỏi thành công!');
      } else {
        await api.adminCreateQuestion({
          position_id: formData.position_id || filterPositionId,
          category: formData.category,
          question_text: formData.question_text,
          time_limit_seconds: Number(formData.time_limit_seconds),
          level: formData.level,
          levels: levelsArray.length > 0 ? levelsArray : [formData.level],
        });
        showNotification('Thêm câu hỏi mới thành công!');
      }
      setModalType(null);
      loadQuestions();
    } catch (err) {
      console.error('Lỗi lưu câu hỏi:', err);
      showNotification(err.response?.data?.detail || 'Thao tác câu hỏi thất bại.', true);
    }
  };

  const handleDeleteQuestion = async (q) => {
    if (!window.confirm('Bạn có chắc muốn xóa câu hỏi này khỏi ngân hàng câu hỏi?')) return;
    try {
      await api.adminDeleteQuestion(q.id);
      showNotification('Đã xóa câu hỏi thành công!');
      loadQuestions();
    } catch (err) {
      console.error('Lỗi xóa câu hỏi:', err);
      showNotification('Không thể xóa câu hỏi.', true);
    }
  };

  // ----------------------------------------------------------------------
  // HANDLERS: INDUSTRIES
  // ----------------------------------------------------------------------
  const handleOpenIndustryModal = (ind = null) => {
    if (ind) {
      setEditingItem(ind);
      setFormData({ name: ind.name, code: ind.code });
      setModalType('edit_industry');
    } else {
      setEditingItem(null);
      setFormData({ name: '', code: '' });
      setModalType('create_industry');
    }
  };

  const handleSaveIndustry = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.adminUpdateIndustry(editingItem.id, {
          name: formData.name,
          code: formData.code,
        });
        showNotification('Cập nhật ngành nghề thành công!');
      } else {
        await api.adminCreateIndustry({
          name: formData.name,
          code: formData.code.toUpperCase().replace(/\s+/g, '_'),
        });
        showNotification('Thêm ngành nghề mới thành công!');
      }
      setModalType(null);
      const updatedInd = await api.adminGetIndustries();
      setIndustries(updatedInd);
    } catch (err) {
      console.error('Lỗi lưu ngành nghề:', err);
      showNotification(err.response?.data?.detail || 'Thao tác ngành nghề thất bại.', true);
    }
  };

  const handleDeleteIndustry = async (ind) => {
    if (!window.confirm(`Bạn có chắc muốn xóa ngành nghề "${ind.name}"?`)) return;
    try {
      await api.adminDeleteIndustry(ind.id);
      showNotification('Đã xóa ngành nghề thành công!');
      const updated = await api.adminGetIndustries();
      setIndustries(updated);
    } catch (err) {
      console.error('Lỗi xóa ngành nghề:', err);
      showNotification(err.response?.data?.detail || 'Không thể xóa: Có vị trí trực thuộc đang hoạt động.', true);
    }
  };

  // ----------------------------------------------------------------------
  // HANDLERS: SEGMENTS
  // ----------------------------------------------------------------------
  const handleOpenSegmentModal = (seg = null) => {
    if (seg) {
      setEditingItem(seg);
      setFormData({
        name: seg.name,
        code: seg.code || '',
        description: seg.description || '',
        industry_id: seg.industry_id || (industries[0]?.id || ''),
        position_id: seg.position_id || (positions[0]?.id || ''),
        sort_order: seg.sort_order || 0,
      });
      setModalType('edit_segment');
    } else {
      setEditingItem(null);
      setFormData({
        name: '',
        code: '',
        description: '',
        industry_id: industries[0]?.id || '',
        position_id: positions[0]?.id || '',
        sort_order: 0,
      });
      setModalType('create_segment');
    }
  };

  const handleSaveSegment = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.updateSegment(editingItem.id, {
          name: formData.name,
          code: formData.code,
          description: formData.description,
          industry_id: formData.industry_id,
          position_id: formData.position_id,
          sort_order: Number(formData.sort_order) || 0,
        });
        showNotification('Cập nhật phân khúc thành công!');
      } else {
        await api.createSegment({
          name: formData.name,
          code: formData.code || formData.name.toLowerCase().replace(/\s+/g, '-'),
          description: formData.description,
          industry_id: formData.industry_id,
          position_id: formData.position_id,
          sort_order: Number(formData.sort_order) || 0,
        });
        showNotification('Thêm phân khúc mới thành công!');
      }
      setModalType(null);
      loadSegments();
    } catch (err) {
      console.error('Lỗi lưu phân khúc:', err);
      showNotification(err.response?.data?.detail || 'Thao tác phân khúc thất bại.', true);
    }
  };

  const handleDeleteSegment = async (seg) => {
    if (!window.confirm(`Bạn có chắc muốn xóa phân khúc "${seg.name}"?`)) return;
    try {
      await api.deleteSegment(seg.id);
      showNotification('Đã xóa phân khúc thành công!');
      loadSegments();
    } catch (err) {
      console.error('Lỗi xóa phân khúc:', err);
      showNotification('Không thể xóa phân khúc.', true);
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
            Quản trị Tuyển dụng & Ngân hàng Đề thi
          </h1>
          <p style={{ color: '#64748b', fontSize: '14px', margin: '4px 0 0 0' }}>
            Thiết lập danh mục vị trí, ngân hàng câu hỏi AI, ngành nghề và phân khúc chuyên môn.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertCircle size={16} />
          <span style={{ fontSize: '14px' }}>{error}</span>
        </div>
      )}
      {successMsg && (
        <div style={{ padding: '12px 16px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <CheckCircle2 size={16} />
          <span style={{ fontSize: '14px' }}>{successMsg}</span>
        </div>
      )}

      {/* 4 Tabs Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #e2e8f0', marginBottom: '24px' }}>
        {[
          { id: 'positions', label: 'Vị trí tuyển dụng', icon: Briefcase },
          { id: 'questions', label: 'Ngân hàng câu hỏi', icon: HelpCircle },
          { id: 'industries', label: 'Ngành nghề', icon: FolderTree },
          { id: 'segments', label: 'Phân khúc chuyên môn', icon: Layers },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 20px',
                border: 'none',
                background: 'transparent',
                borderBottom: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                color: isActive ? '#3b82f6' : '#64748b',
                fontWeight: isActive ? 700 : 500,
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: POSITIONS */}
      {/* ========================================================================= */}
      {activeTab === 'positions' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#334155' }}>
              Danh sách Vị trí tuyển dụng ({positions.length})
            </div>
            <button
              onClick={() => handleOpenPositionModal()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '9px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <Plus size={16} /> Thêm Vị trí mới
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            {positions.map((pos) => (
              <div key={pos.id} className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 600, background: '#f1f5f9', color: '#475569', padding: '3px 8px', borderRadius: '6px' }}>
                      {pos.industry_name}
                    </span>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => handleOpenPositionModal(pos)}
                        style={{ background: '#f1f5f9', border: 'none', padding: '5px', borderRadius: '6px', color: '#64748b', cursor: 'pointer' }}
                        title="Chỉnh sửa"
                      >
                        <Edit size={14} />
                      </button>
                      <button
                        onClick={() => handleDeletePosition(pos)}
                        style={{ background: '#fef2f2', border: 'none', padding: '5px', borderRadius: '6px', color: '#ef4444', cursor: 'pointer' }}
                        title="Xóa"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 6px 0' }}>
                    {pos.name}
                  </h3>
                  <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px' }}>
                    Thời lượng: {pos.duration || '3–6 tháng'} | Icon: {pos.icon || 'server'}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                    {(pos.skills || []).map((sk, idx) => (
                      <span key={idx} style={{ background: '#eff6ff', color: '#2563eb', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 500 }}>
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Ngân hàng câu hỏi: <strong style={{ color: '#0f172a' }}>{pos.question_count || 0}</strong>
                  </span>
                  <button
                    onClick={() => {
                      setFilterPositionId(pos.id);
                      setActiveTab('questions');
                    }}
                    style={{ background: 'transparent', border: 'none', color: '#3b82f6', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Xem câu hỏi &rarr;
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: QUESTIONS BANK */}
      {/* ========================================================================= */}
      {activeTab === 'questions' && (
        <div>
          {/* Filter Bar */}
          <div className="panel" style={{ padding: '16px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>
                <Filter size={16} /> Lọc câu hỏi:
              </div>
              <select
                value={filterPositionId}
                onChange={(e) => setFilterPositionId(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', outline: 'none' }}
              >
                {positions.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>

              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', outline: 'none' }}
              >
                <option value="">Tất cả Level</option>
                <option value="intern">Intern</option>
                <option value="fresher">Fresher</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
              </select>
            </div>

            <button
              onClick={() => handleOpenQuestionModal()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '9px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <Plus size={16} /> Thêm câu hỏi
            </button>
          </div>

          {/* Questions Table */}
          <div className="panel" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <th style={{ padding: '14px 18px', color: '#64748b', fontSize: '12px', fontWeight: 600, width: '120px' }}>PHÂN LOẠI</th>
                  <th style={{ padding: '14px 18px', color: '#64748b', fontSize: '12px', fontWeight: 600 }}>NỘI DUNG CÂU HỎI</th>
                  <th style={{ padding: '14px 18px', color: '#64748b', fontSize: '12px', fontWeight: 600, width: '130px' }}>LEVEL ÁP DỤNG</th>
                  <th style={{ padding: '14px 18px', color: '#64748b', fontSize: '12px', fontWeight: 600, width: '90px' }}>THỜI LƯỢNG</th>
                  <th style={{ padding: '14px 18px', textAlign: 'right', width: '90px' }}>THAO TÁC</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="5" style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>Đang nạp câu hỏi...</td>
                  </tr>
                ) : questions.length > 0 ? (
                  questions.map((q) => (
                    <tr key={q.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '14px 18px' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: 600,
                          background: q.category === 'Hành vi' ? '#fef3c7' : '#e0e7ff',
                          color: q.category === 'Hành vi' ? '#92400e' : '#3730a3',
                        }}>
                          {q.category || 'Chuyên môn'}
                        </span>
                        <div style={{ marginTop: '4px' }}>
                          <span style={{
                            fontSize: '10px',
                            fontWeight: 600,
                            color: q.source === 'Q-JD' ? '#166534' : '#64748b',
                            background: q.source === 'Q-JD' ? '#dcfce7' : '#f1f5f9',
                            padding: '1px 6px',
                            borderRadius: '4px',
                          }}>
                            {q.source || 'DEFAULT'}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '14px 18px', fontSize: '14px', color: '#0f172a', fontWeight: 500, lineHeight: 1.5 }}>
                        {q.question_text}
                      </td>
                      <td style={{ padding: '14px 18px', fontSize: '12px', color: '#475569' }}>
                        {Array.isArray(q.levels) && q.levels.length > 0 ? q.levels.join(', ') : (q.level || 'junior')}
                      </td>
                      <td style={{ padding: '14px 18px', fontSize: '13px', color: '#64748b' }}>
                        {q.time_limit_seconds || 120}s
                      </td>
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                          <button
                            onClick={() => handleOpenQuestionModal(q)}
                            style={{ background: '#f1f5f9', border: 'none', padding: '5px', borderRadius: '6px', color: '#64748b', cursor: 'pointer' }}
                            title="Sửa câu hỏi"
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            onClick={() => handleDeleteQuestion(q)}
                            style={{ background: '#fef2f2', border: 'none', padding: '5px', borderRadius: '6px', color: '#ef4444', cursor: 'pointer' }}
                            title="Xóa câu hỏi"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                      Chưa có câu hỏi nào trong bộ lọc này. Hãy thêm mới!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: INDUSTRIES */}
      {/* ========================================================================= */}
      {activeTab === 'industries' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#334155' }}>
              Danh mục Ngành nghề ({industries.length})
            </div>
            <button
              onClick={() => handleOpenIndustryModal()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '9px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <Plus size={16} /> Thêm Ngành nghề
            </button>
          </div>

          <div className="panel" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>TÊN NGÀNH NGHỀ</th>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>MÃ NGÀNH</th>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>SỐ VỊ TRÍ TRỰC THUỘC</th>
                  <th style={{ padding: '14px 20px', textAlign: 'right' }}>THAO TÁC</th>
                </tr>
              </thead>
              <tbody>
                {industries.map((ind) => (
                  <tr key={ind.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '14px 20px', fontWeight: 600, color: '#0f172a' }}>{ind.name}</td>
                    <td style={{ padding: '14px 20px', fontSize: '13px', color: '#475569' }}>
                      <code>{ind.code}</code>
                    </td>
                    <td style={{ padding: '14px 20px', fontSize: '14px' }}>
                      <span style={{ background: '#eff6ff', color: '#2563eb', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600 }}>
                        {ind.position_count || 0} vị trí
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                        <button
                          onClick={() => handleOpenIndustryModal(ind)}
                          style={{ background: '#f1f5f9', border: 'none', padding: '6px', borderRadius: '6px', color: '#64748b', cursor: 'pointer' }}
                          title="Sửa tên ngành"
                        >
                          <Edit size={14} />
                        </button>
                        <button
                          onClick={() => handleDeleteIndustry(ind)}
                          style={{ background: '#fef2f2', border: 'none', padding: '6px', borderRadius: '6px', color: '#ef4444', cursor: 'pointer' }}
                          title="Xóa ngành"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: SEGMENTS */}
      {/* ========================================================================= */}
      {activeTab === 'segments' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#334155' }}>
              Phân khúc Chuyên môn ({segments.length})
            </div>
            <button
              onClick={() => handleOpenSegmentModal()}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: '#3b82f6',
                color: '#fff',
                border: 'none',
                padding: '9px 16px',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <Plus size={16} /> Thêm Phân khúc
            </button>
          </div>

          <div className="panel" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>TÊN PHÂN KHÚC</th>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>MÃ CODE</th>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>MÔ TẢ</th>
                  <th style={{ padding: '14px 20px', color: '#64748b', fontSize: '13px', fontWeight: 600 }}>THỨ TỰ</th>
                  <th style={{ padding: '14px 20px', textAlign: 'right' }}>THAO TÁC</th>
                </tr>
              </thead>
              <tbody>
                {segments.length > 0 ? (
                  segments.map((seg) => (
                    <tr key={seg.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '14px 20px', fontWeight: 600, color: '#0f172a' }}>{seg.name}</td>
                      <td style={{ padding: '14px 20px', fontSize: '13px', color: '#475569' }}>
                        <code>{seg.code || '---'}</code>
                      </td>
                      <td style={{ padding: '14px 20px', fontSize: '13px', color: '#64748b' }}>
                        {seg.description || 'Chưa có mô tả'}
                      </td>
                      <td style={{ padding: '14px 20px', fontSize: '13px', color: '#475569' }}>
                        {seg.sort_order ?? 0}
                      </td>
                      <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                          <button
                            onClick={() => handleOpenSegmentModal(seg)}
                            style={{ background: '#f1f5f9', border: 'none', padding: '6px', borderRadius: '6px', color: '#64748b', cursor: 'pointer' }}
                            title="Sửa phân khúc"
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            onClick={() => handleDeleteSegment(seg)}
                            style={{ background: '#fef2f2', border: 'none', padding: '6px', borderRadius: '6px', color: '#ef4444', cursor: 'pointer' }}
                            title="Xóa phân khúc"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                      Chưa có phân khúc nào. Hãy thêm mới!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* POPUP MODALS */}
      {/* ========================================================================= */}
      {modalType && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px',
        }}>
          <div style={{
            background: '#fff',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '560px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
          }}>
            {/* Modal Header */}
            <div style={{ padding: '18px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                {modalType === 'create_position' && 'Thêm Vị trí tuyển dụng mới'}
                {modalType === 'edit_position' && 'Chỉnh sửa Vị trí tuyển dụng'}
                {modalType === 'create_question' && 'Thêm Câu hỏi mới vào Ngân hàng'}
                {modalType === 'edit_question' && 'Chỉnh sửa Câu hỏi'}
                {modalType === 'create_industry' && 'Thêm Ngành nghề mới'}
                {modalType === 'edit_industry' && 'Chỉnh sửa Ngành nghề'}
                {modalType === 'create_segment' && 'Thêm Phân khúc mới'}
                {modalType === 'edit_segment' && 'Chỉnh sửa Phân khúc'}
              </h3>
              <button
                onClick={() => setModalType(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={
              modalType.includes('position')
                ? handleSavePosition
                : modalType.includes('question')
                ? handleSaveQuestion
                : modalType.includes('industry')
                ? handleSaveIndustry
                : handleSaveSegment
            } style={{ padding: '24px' }}>
              
              {/* Form Fields: Position */}
              {modalType.includes('position') && (
                <>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Ngành nghề *</label>
                    <select
                      value={formData.industry_id}
                      onChange={(e) => setFormData({ ...formData, industry_id: e.target.value })}
                      required
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    >
                      {industries.map((ind) => (
                        <option key={ind.id} value={ind.id}>{ind.name}</option>
                      ))}
                    </select>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Tên vị trí tuyển dụng *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ví dụ: Backend Developer, AI Engineer..."
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Mã định danh (Code)</label>
                      <input
                        type="text"
                        placeholder="backend, ai-eng..."
                        value={formData.code || ''}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Thời lượng gợi ý</label>
                      <input
                        type="text"
                        placeholder="3–6 tháng, 1–3 năm..."
                        value={formData.duration || ''}
                        onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      />
                    </div>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Kỹ năng yêu cầu (phân cách bởi dấu phẩy)</label>
                    <input
                      type="text"
                      placeholder="Python, Django, PostgreSQL, Docker..."
                      value={formData.skills || ''}
                      onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                </>
              )}

              {/* Form Fields: Question */}
              {modalType.includes('question') && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Phân loại câu hỏi *</label>
                      <select
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      >
                        <option value="Chuyên môn">Chuyên môn</option>
                        <option value="Hành vi">Hành vi</option>
                        <option value="Tình huống">Tình huống</option>
                        <option value="Thiết kế">Thiết kế hệ thống</option>
                        <option value="Lãnh đạo">Lãnh đạo / Teamwork</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Thời lượng trả lời (giây)</label>
                      <input
                        type="number"
                        min="30"
                        max="300"
                        value={formData.time_limit_seconds || 120}
                        onChange={(e) => setFormData({ ...formData, time_limit_seconds: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Level áp dụng (phân cách bởi dấu phẩy) *</label>
                    <input
                      type="text"
                      placeholder="intern, fresher, junior, mid, senior"
                      value={formData.levels || ''}
                      onChange={(e) => setFormData({ ...formData, levels: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Nội dung câu hỏi phỏng vấn *</label>
                    <textarea
                      required
                      rows={4}
                      placeholder="Nhập nội dung câu hỏi chi tiết..."
                      value={formData.question_text || ''}
                      onChange={(e) => setFormData({ ...formData, question_text: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', resize: 'vertical' }}
                    />
                  </div>
                </>
              )}

              {/* Form Fields: Industry */}
              {modalType.includes('industry') && (
                <>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Tên Ngành nghề *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ví dụ: Công nghệ thông tin, Tài chính ngân hàng..."
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Mã Ngành (Code) *</label>
                    <input
                      type="text"
                      required
                      placeholder="IT, FIN, SALES, HR..."
                      value={formData.code || ''}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                </>
              )}

              {/* Form Fields: Segment */}
              {modalType.includes('segment') && (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Ngành nghề *</label>
                      <select
                        value={formData.industry_id}
                        onChange={(e) => setFormData({ ...formData, industry_id: e.target.value })}
                        required
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      >
                        {industries.map((ind) => (
                          <option key={ind.id} value={ind.id}>{ind.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Vị trí trực thuộc *</label>
                      <select
                        value={formData.position_id}
                        onChange={(e) => setFormData({ ...formData, position_id: e.target.value })}
                        required
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      >
                        {positions.map((pos) => (
                          <option key={pos.id} value={pos.id}>{pos.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Tên Phân khúc *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ví dụ: Backend Python / Django..."
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Mã Code</label>
                      <input
                        type="text"
                        placeholder="seg-be-py"
                        value={formData.code || ''}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Thứ tự sắp xếp</label>
                      <input
                        type="number"
                        value={formData.sort_order ?? 0}
                        onChange={(e) => setFormData({ ...formData, sort_order: e.target.value })}
                        style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                      />
                    </div>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>Mô tả chi tiết</label>
                    <textarea
                      rows={2}
                      placeholder="Mô tả phạm vi kiến thức chuyên môn của phân khúc..."
                      value={formData.description || ''}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      style={{ width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none' }}
                    />
                  </div>
                </>
              )}

              {/* Form Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
                <button
                  type="button"
                  onClick={() => setModalType(null)}
                  style={{ padding: '9px 18px', background: '#e2e8f0', color: '#475569', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  style={{ padding: '9px 20px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                >
                  Lưu thay đổi
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
