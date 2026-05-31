import React, { useState, useRef, useEffect, useCallback } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { streamChat } from '../api/api';
import ProductCard from './cards/ProductCard';
import CompatBadge from './cards/CompatBadge';
import InstallChecklist from './cards/InstallChecklist';
import TroubleshootCard from './cards/TroubleshootCard';
import ValidatorBadge from './cards/ValidatorBadge';
import EscalationBanner from './cards/EscalationBanner';
import './ChatWindow.css';

marked.setOptions({ breaks: true, gfm: true });

const WELCOME_MSG = {
  role: 'assistant',
  content:
    'Hi! I can help you find refrigerator and dishwasher parts, check ' +
    'compatibility, troubleshoot symptoms, and track orders. What can I help you with today?',
  cards: [],
  validator: null,
  modelNumber: null,
  applianceType: null,
  isStreaming: false,
  hasToolCalls: false,
};

const QUICK_ACTIONS = [
  { label: 'Install a part', prompt: 'How can I install part number ' },
  {
    label: 'Check compatibility',
    prompt: 'Check compatibility for part number  and model ',
  },
  {
    label: 'Diagnose a problem',
    prompt: 'My refrigerator/dishwasher is ',
  },
  { label: 'Track order', prompt: 'I want to track my order. My order number is ' },
];

// ---------------------------------------------------------------------------
// Tool result → card data
// ---------------------------------------------------------------------------

function parseToolResults(toolResults = []) {
  const cards = [];
  for (const result of toolResults) {
    let data;
    try { data = JSON.parse(result.content); } catch { continue; }
    if (!data) continue;

    switch (result.name) {
      case 'search_parts_tool':
        if (Array.isArray(data))
          data.slice(0, 3).forEach((p) => cards.push({ type: 'product', data: p }));
        break;
      case 'get_part_detail_tool':
        if (data && typeof data === 'object' && !Array.isArray(data))
          cards.push({ type: 'product', data });
        break;
      case 'get_cart_deep_link_tool':
        if (data && typeof data === 'object' && data.part_number) {
          cards.push({ type: 'cart', data });
        }
        break;
      case 'check_compatibility_tool':
        if (data && typeof data === 'object')
          cards.push({ type: 'compat', data });
        break;
      case 'get_install_guide_tool':
        if (Array.isArray(data) && data.length) {
          cards.push({ type: 'install', data: { steps: data } });
        } else if (data?.steps?.length) {
          cards.push({ type: 'install', data });
        }
        break;
      case 'diagnose_symptom_tool':
        if (Array.isArray(data) && data.length)
          cards.push({ type: 'troubleshoot', data });
        break;
      default:
        break;
    }
  }
  return cards;
}

function renderCard(card, i) {
  switch (card.type) {
    case 'product':      return <ProductCard      key={i} part={card.data} />;
    case 'compat':       return <CompatBadge      key={i} data={card.data} />;
    case 'install':      return <InstallChecklist key={i} data={card.data} />;
    case 'troubleshoot': return <TroubleshootCard key={i} data={card.data} />;
    case 'cart':         return <ProductCard      key={i} part={card.data} />;
    default:             return null;
  }
}

// ---------------------------------------------------------------------------
// ChatWindow
// ---------------------------------------------------------------------------

export default function ChatWindow() {
  const [messages, setMessages]         = useState([WELCOME_MSG]);
  const [input, setInput]               = useState('');
  const [isLoading, setIsLoading]       = useState(false);
  const [conversationId, setConvId]     = useState(null);
  const bottomRef  = useRef(null);
  const cleanupRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Close any open stream when the component unmounts
  useEffect(() => () => cleanupRef.current?.(), []);

  // Functional update for the last message in the array
  const updateLast = useCallback((updater) => {
    setMessages((prev) => {
      const msgs = [...prev];
      msgs[msgs.length - 1] = updater({ ...msgs[msgs.length - 1] });
      return msgs;
    });
  }, []);

  const handleSend = (overrideText = null) => {
    const sourceText = typeof overrideText === 'string' ? overrideText : input;
    const text = sourceText.trim();
    if (!text || isLoading) return;

    cleanupRef.current?.();
    cleanupRef.current = null;

    setInput('');
    setIsLoading(true);

    // Add user + empty assistant placeholder in one update to avoid index drift
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: text },
      {
        role: 'assistant',
        content: '',
        cards: [],
        validator: null,
        modelNumber: null,
        applianceType: null,
        isStreaming: true,
        hasToolCalls: false,
      },
    ]);

    const cleanup = streamChat(text, conversationId, {
      onSupervisor: (data) =>
        updateLast((msg) => ({
          ...msg,
          applianceType: data.appliance_type,
          modelNumber: data.model_number,
        })),

      onSpecialist: (data) => {
        if (data.content) {
          updateLast((msg) => ({ ...msg, content: data.content, hasToolCalls: false }));
        } else if (data.tool_calls?.length) {
          updateLast((msg) => ({ ...msg, hasToolCalls: true }));
        }
      },

      onToolNode: (data) => {
        const newCards = parseToolResults(data.tool_results);
        updateLast((msg) => ({
          ...msg,
          hasToolCalls: false,
          cards: [...msg.cards, ...newCards],
        }));
      },

      onValidator: (data) =>
        updateLast((msg) => ({
          ...msg,
          validator: { verdict: data.verdict, feedback: data.feedback },
          ...(data.override_content ? { content: data.override_content } : {}),
        })),

      onDone: (data) => {
        if (data.conversation_id) setConvId(data.conversation_id);
        updateLast((msg) => ({ ...msg, isStreaming: false }));
        setIsLoading(false);
      },

      onError: () => {
        updateLast((msg) => ({
          ...msg,
          content: 'Sorry, something went wrong. Please try again.',
          isStreaming: false,
        }));
        setIsLoading(false);
      },
    });

    cleanupRef.current = cleanup;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  const handleQuickAction = (prompt) => {
    if (isLoading) return;
    setInput(prompt);
  };

  const renderMarkdown = (content) => ({
    __html: DOMPurify.sanitize(marked.parse(content)),
  });

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === 'user' ? (
              <div className="message-bubble">{msg.content}</div>
            ) : (
              <div className="message-bubble">
                {/* Loading states */}
                {msg.isStreaming && !msg.content && !msg.hasToolCalls && (
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                )}
                {msg.isStreaming && msg.hasToolCalls && (
                  <div className="tool-status">Looking up parts&hellip;</div>
                )}

                {/* Main answer text */}
                {msg.content && (
                  <div
                    className="message-text"
                    dangerouslySetInnerHTML={renderMarkdown(msg.content)}
                  />
                )}

                {/* Detected model chip */}
                {msg.modelNumber && (
                  <div className="model-chip">
                    Detected model: <strong>{msg.modelNumber}</strong>
                    {msg.applianceType && msg.applianceType !== 'unknown' && (
                      <span className="appliance-chip"> ({msg.applianceType})</span>
                    )}
                  </div>
                )}

                {/* Structured result cards */}
                {msg.cards.length > 0 && (
                  <div className="cards-container">
                    {msg.cards.map((card, ci) => renderCard(card, ci))}
                  </div>
                )}

                {/* Validator verdict */}
                {msg.validator && msg.validator.verdict !== 'escalate' && (
                  <ValidatorBadge
                    verdict={msg.validator.verdict}
                    feedback={msg.validator.feedback}
                  />
                )}
                {msg.validator?.verdict === 'escalate' && <EscalationBanner />}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <div className="quick-actions" aria-label="Common PartSelect assistant actions">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              type="button"
              className="quick-action-btn"
              onClick={() => handleQuickAction(action.prompt)}
              disabled={isLoading}
            >
              {action.label}
            </button>
          ))}
        </div>
        <textarea
          value={input}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about parts, compatibility, installation, or your order…"
          rows={1}
          disabled={isLoading}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '…' : 'Send'}
        </button>
      </div>
    </div>
  );
}
