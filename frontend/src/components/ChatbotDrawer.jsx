import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Bot,
  History,
  MessageSquarePlus,
  Send,
  Sparkles,
  Trash2,
  X,
  ChevronLeft,
} from 'lucide-react';
import { api } from '../services/api';
import { ADVISOR, analyzeHistory } from '../services/agentMock';

// Hỗ trợ **in đậm** và *in nghiêng* đơn giản
const renderInline = (text) =>
  text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).map((part, i) => {
    if (part.startsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>;
    return part;
  });

const newId = () => `conv_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
const formatDate = (iso) =>
  new Date(iso).toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
const makeTitle = (text) => (text.length > 36 ? `${text.slice(0, 36)}…` : text);

export default function ChatbotDrawer({ isOpen, onClose, sessionId = null }) {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [draft, setDraft] = useState(null);
  const [suggestions, setSuggestions] = useState(ADVISOR.suggestions);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [showHistoryView, setShowHistoryView] = useState(false);
  const [sessions, setSessions] = useState([]);
  const endRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    // Tải danh sách hội thoại
    api.listConversations().then((list) => {
      setConversations(list);
      if (list[0] && !activeId) setActiveId(list[0].id);
    });
    // Tải lịch sử phỏng vấn để phân tích summary
    api.getSessionHistory().then((data) => {
      setSessions(data || []);
    });
  }, [isOpen]);

  const active = conversations.find((c) => c.id === activeId) || draft;
  const messages = active?.messages || [];
  const summary = analyzeHistory(sessions);

  useEffect(() => {
    if (isOpen && !showHistoryView) {
      endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages.length, sending, activeId, isOpen, showHistoryView]);

  const startNew = useCallback(() => {
    setActiveId(null);
    setDraft(null);
    setSuggestions(ADVISOR.suggestions);
    setShowHistoryView(false);
  }, []);

  const selectConv = (id) => {
    setActiveId(id);
    setDraft(null);
    setSuggestions(ADVISOR.suggestions);
    setShowHistoryView(false);
  };

  const upsert = (conv) => {
    setConversations((prev) => [conv, ...prev.filter((c) => c.id !== conv.id)]);
    api.saveConversation(conv);
  };

  const send = async (text) => {
    const content = text.trim();
    if (!content || sending) return;
    const now = new Date().toISOString();
    const base = active || {
      id: newId(),
      title: makeTitle(content),
      created_at: now,
      messages: [],
    };
    const userConv = {
      ...base,
      updated_at: now,
      messages: [...base.messages, { role: 'user', content, at: now }],
    };
    setActiveId(userConv.id);
    setDraft(null);
    upsert(userConv);
    setInput('');
    setSending(true);
    try {
      const res = await api.chatWithAgent({
        conversationId: userConv.id,
        sessionId,
        message: content,
        history: base.messages,
      });
      const doneAt = new Date().toISOString();
      upsert({
        ...userConv,
        updated_at: doneAt,
        messages: [
          ...userConv.messages,
          { role: 'agent', content: res.reply, at: doneAt },
        ],
      });
      setSuggestions(res.suggestions || []);
    } catch {
      const doneAt = new Date().toISOString();
      upsert({
        ...userConv,
        updated_at: doneAt,
        messages: [
          ...userConv.messages,
          {
            role: 'agent',
            content: 'Xin lỗi, đã có lỗi kết nối. Bạn thử lại nhé.',
            error: true,
            at: doneAt,
          },
        ],
      });
    } finally {
      setSending(false);
    }
  };

  const remove = (id) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    api.deleteConversation(id);
    if (id === activeId) startNew();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="cb-backdrop" onClick={onClose} />
      <aside className="cb-drawer" aria-label="AI Cố vấn phỏng vấn">
        {/* Drawer Header */}
        <div className="cb-header">
          <div className="cb-header-left">
            <span className="cb-avatar"><Bot size={18} /></span>
            <div>
              <div className="cb-title">AI Cố vấn phỏng vấn</div>
              <div className="cb-status">
                <span className="cb-online-dot" /> Đang hoạt động
              </div>
            </div>
          </div>

          <div className="cb-header-actions">
            <button
              className={`cb-icon-btn ${showHistoryView ? 'active' : ''}`}
              title="Lịch sử cuộc trò chuyện"
              onClick={() => setShowHistoryView((prev) => !prev)}
            >
              <History size={16} />
            </button>
            <button
              className="cb-icon-btn"
              title="Cuộc trò chuyện mới"
              onClick={startNew}
            >
              <MessageSquarePlus size={16} />
            </button>
            <button
              className="cb-icon-btn cb-close-btn"
              title="Đóng (Esc)"
              onClick={onClose}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* View Danh sách Lịch sử trò chuyện */}
        {showHistoryView ? (
          <div className="cb-history-view">
            <div className="cb-history-head">
              <button
                className="cb-back-btn"
                onClick={() => setShowHistoryView(false)}
              >
                <ChevronLeft size={16} /> Quay lại đoạn chat
              </button>
              <span className="cb-history-count">
                {conversations.length} cuộc hội thoại
              </span>
            </div>

            <div className="cb-history-list">
              {conversations.length === 0 ? (
                <div className="cb-empty">Chưa có cuộc trò chuyện nào được lưu.</div>
              ) : (
                conversations.map((c) => (
                  <div
                    key={c.id}
                    className={`cb-history-item ${c.id === activeId ? 'active' : ''}`}
                  >
                    <button
                      className="cb-history-main"
                      onClick={() => selectConv(c.id)}
                    >
                      <span className="cb-history-title">{c.title}</span>
                      <span className="cb-history-date">
                        {formatDate(c.updated_at)} · {c.messages?.length || 0} tin nhắn
                      </span>
                    </button>
                    <button
                      className="cb-history-del"
                      onClick={() => remove(c.id)}
                      title="Xóa hội thoại"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : (
          <>
            {/* 4 Summary Badges */}
            {summary && (
              <div className="cb-insight-grid">
                <div className="cb-insight-card">
                  <span className="cb-insight-label">Điểm TB</span>
                  <strong className="cb-insight-val">{summary.average}</strong>
                </div>
                <div className="cb-insight-card">
                  <span className="cb-insight-label">Xu hướng</span>
                  <strong
                    className={`cb-insight-val ${
                      summary.trend >= 0 ? 'up' : 'down'
                    }`}
                  >
                    {summary.trend >= 0 ? '+' : ''}
                    {summary.trend}
                  </strong>
                </div>
                <div className="cb-insight-card">
                  <span className="cb-insight-label">Điểm mạnh</span>
                  <strong className="cb-insight-val" title={summary.best.label}>
                    {summary.best.label}
                  </strong>
                </div>
                <div className="cb-insight-card">
                  <span className="cb-insight-label">Cần cải thiện</span>
                  <strong className="cb-insight-val" title={summary.worst.label}>
                    {summary.worst.label}
                  </strong>
                </div>
              </div>
            )}

            {/* Khung tin nhắn */}
            <div className="cb-messages">
              <div className="cb-msg cb-msg-agent">
                <span className="cb-msg-avatar"><Sparkles size={14} /></span>
                <div className="cb-bubble">{ADVISOR.welcome}</div>
              </div>

              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`cb-msg ${m.role === 'user' ? 'cb-msg-user' : 'cb-msg-agent'}`}
                >
                  {m.role === 'agent' && (
                    <span className="cb-msg-avatar"><Sparkles size={14} /></span>
                  )}
                  <div className={`cb-bubble ${m.error ? 'error' : ''}`}>
                    {m.content.split('\n').map((line, j) => (
                      <p key={j}>{renderInline(line)}</p>
                    ))}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="cb-msg cb-msg-agent">
                  <span className="cb-msg-avatar"><Sparkles size={14} /></span>
                  <div className="cb-bubble typing">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>

            {/* Gợi ý câu hỏi nhanh (Suggestion Chips) */}
            {suggestions.length > 0 && (
              <div className="cb-suggestions">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    className="cb-chip"
                    onClick={() => send(s)}
                    disabled={sending}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Input box cố định chân trang */}
            <form
              className="cb-input-box"
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Hỏi AI về kết quả hoặc kỹ năng cần luyện..."
                disabled={sending}
              />
              <button
                type="submit"
                className="cb-send-btn"
                disabled={!input.trim() || sending}
                title="Gửi"
              >
                <Send size={15} />
              </button>
            </form>
          </>
        )}
      </aside>
    </>
  );
}
