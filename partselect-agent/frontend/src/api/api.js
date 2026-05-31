/**
 * API client for the PartSelect Agent backend.
 * Creates stream sessions with POST, then opens SSE with an opaque token.
 */

const BASE_URL = process.env.REACT_APP_API_URL || '';
const API_KEY = process.env.REACT_APP_API_KEY || '';

const authHeaders = () => (
  API_KEY ? { 'X-API-Key': API_KEY } : {}
);

export function streamChat(message, conversationId = null, handlers = {}) {
  let es = null;
  let cancelled = false;

  fetch(`${BASE_URL}/api/chat/stream-session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  })
    .then((res) => {
      if (!res.ok) throw new Error('stream session failed');
      return res.json();
    })
    .then(({ stream_token: streamToken }) => {
      if (cancelled) return;

      const params = new URLSearchParams({ stream_token: streamToken });
      es = new EventSource(`${BASE_URL}/api/chat/stream?${params.toString()}`);

      const on = (event, handler) => {
        if (!handler) return;
        es.addEventListener(event, (e) => {
          try { handler(JSON.parse(e.data)); } catch { /* ignore malformed events */ }
        });
      };

      on('supervisor', handlers.onSupervisor);
      on('specialist', handlers.onSpecialist);
      on('decline', handlers.onSpecialist);
      on('tool_node', handlers.onToolNode);
      on('validator', handlers.onValidator);

      es.addEventListener('error', (e) => {
        es.close();
        try { handlers.onError?.(JSON.parse(e.data)); } catch { handlers.onError?.(); }
      });

      es.addEventListener('done', (e) => {
        es.close();
        try { handlers.onDone?.(JSON.parse(e.data)); } catch { handlers.onDone?.({}); }
      });

      es.onerror = () => {
        es.close();
        handlers.onError?.();
      };
    })
    .catch(() => handlers.onError?.());

  return () => {
    cancelled = true;
    es?.close();
  };
}

export { BASE_URL, API_KEY };
