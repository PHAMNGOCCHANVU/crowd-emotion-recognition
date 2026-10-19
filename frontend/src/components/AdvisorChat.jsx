import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Bot, MessageSquarePlus, Send, Sparkles, Trash2 } from 'lucide-react';
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
const formatDate = (iso) => new Date(iso).toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
const makeTitle = (text) => (text.length > 40 ? `${text.slice(0, 40)}…` : text);

export default function AdvisorChat({ sessions }) {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [draft, setDraft] = useState(null);
  const [suggestions, setSuggestions] = useState(ADVISOR.suggestions);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    api.listConversations().then((list) => {
      setConversations(list);
      if (list[0]) setActiveId(list[0].id);
    });
  }, []);

  const active = conversations.find((c) => c.id === activeId) || draft;
  const messages = active?.messages || [];
  const summary = analyzeHistory(sessions);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, sending, activeId]);

  const startNew = useCallback(() => {
    setActiveId(null);
    setDraft(null);
    setSuggestions(ADVISOR.suggestions);
  }, []);

  const select = (id) => {
    setActiveId(id);
    setDraft(null);
    setSuggestions(ADVISOR.suggestions);
  };

  const upsert = (conv) => {
    setConversations((prev) => [conv, ...prev.filter((c) => c.id !== conv.id)]);
    api.saveConversation(conv);
  };

  const send = async (text) => {
    const content = text.trim();
    if (!content || sending) return;
    const now = new Date().toISOString();
    const base = active || { id: newId(), title: makeTitle(content), created_at: now, messages: [] };
    const userConv = { ...base, updated_at: now, messages: [...base.messages, { role: 'user', content, at: now }] };
    setActiveId(userConv.id);
    setDraft(null);
    upsert(userConv);
    setInput('');
    setSending(true);
    try {
      const res = await api.chatWithAgent({ conversationId: userConv.id, message: content, history: base.messages });
      const doneAt = new Date().toISOString();
      upsert({ ...userConv, updated_at: doneAt, messages: [...userConv.messages, { role: 'agent', content: res.reply, at: doneAt }] });
      setSuggestions(res.suggestions || []);
    } catch {
      const doneAt = new Date().toISOString();
      upsert({ ...userConv, updated_at: doneAt, messages: [...userConv.messages, { role: 'agent', content: 'Xin lỗi, đã có lỗi xảy ra. Bạn thử lại nhé.', error: true, at: doneAt }] });
    } finally {
      setSending(false);
    }
  };

  const remove = (id) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    api.deleteConversation(id);
    if (id === activeId) startNew();
  };

  return (
    <div className="agent-layout">
      <aside className="agent-side">
        <button className="agent-new" onClick={startNew}><MessageSquarePlus size={15} /> Cuộc trò chuyện mới</button>
        <div className="agent-side-label">Lịch sử trò chuyện</div>
        <div className="agent-convs">
          {conversations.length === 0 && <div className="agent-empty">Chưa có cuộc trò chuyện nào được lưu.</div>}
          {conversations.map((c) => (
            <div key={c.id} className={`agent-conv ${c.id === activeId ? 'active' : ''}`}>
              <button className="agent-conv-main" onClick={() => select(c.id)}>
                <span className="agent-conv-title">{c.title}</span>
                <span className="agent-conv-date">{formatDate(c.updated_at)} · {c.messages.length} tin nhắn</span>
              </button>
              <button className="agent-conv-del" onClick={() => remove(c.id)} title="Xóa"><Trash2 size={13} /></button>
            </div>
          ))}
        </div>
      </aside>

      <section className="agent-chat">
        <div className="agent-chat-header">
          <span className="agent-avatar"><Bot size={18} /></span>
          <div className="agent-chat-title">
            <strong>AI Cố vấn phỏng vấn</strong>
            <span><i className="agent-online" /> {summary ? `Đang phân tích ${summary.total} phiên của bạn` : 'Chưa có dữ liệu phiên'}</span>
          </div>
        </div>

        {summary && (
          <div className="agent-insight">
            <div><span>Điểm TB</span><strong>{summary.average}</strong></div>
            <div><span>Xu hướng</span><strong className={summary.trend >= 0 ? 'up' : 'down'}>{summary.trend >= 0 ? '+' : ''}{summary.trend}</strong></div>
            <div><span>Mạnh nhất</span><strong>{summary.best.label}</strong></div>
            <div><span>Cần cải thiện</span><strong>{summary.worst.label}</strong></div>
          </div>
        )}

        <div className="agent-messages">
          <div className="agent-msg agent">
            <span className="agent-avatar sm"><Sparkles size={13} /></span>
            <div className="agent-bubble">{ADVISOR.welcome}</div>
          </div>
          {messages.map((m, i) => (
            <div key={i} className={`agent-msg ${m.role}`}>
              {m.role === 'agent' && <span className="agent-avatar sm"><Sparkles size={13} /></span>}
              <div className={`agent-bubble ${m.error ? 'error' : ''}`}>
                {m.content.split('\n').map((line, j) => <p key={j}>{renderInline(line)}</p>)}
              </div>
            </div>
          ))}
          {sending && (
            <div className="agent-msg agent">
              <span className="agent-avatar sm"><Sparkles size={13} /></span>
              <div className="agent-bubble typing"><i /><i /><i /></div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {suggestions.length > 0 && (
          <div className="agent-suggestions">
            {suggestions.map((s) => (
              <button key={s} className="agent-chip" onClick={() => send(s)} disabled={sending}>{s}</button>
            ))}
          </div>
        )}

        <form className="agent-input" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Hỏi AI về kết quả luyện tập của bạn..." />
          <button type="submit" className="primary-button" disabled={!input.trim() || sending}><Send size={15} /></button>
        </form>
      </section>
    </div>
  );
}
