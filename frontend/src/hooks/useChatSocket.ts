// hooks/useChatSocket.ts
//
// Core chat hook — manages messages, conversation session, and backend communication.
//
// Responsibilities:
//   - Track current conversation ID (created by backend on first message)
//   - Send messages to POST /api/chat and receive reply + insights
//   - Load a previous conversation from GET /api/conversations/:id
//   - Start a fresh new chat session

import { useState, useCallback, useEffect, useRef } from 'react';

export interface Insights {
  intent: string;    // complaint | query | request | greeting | general
  sentiment: string; // positive | neutral | negative
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  insights?: Insights;      // Present on assistant messages
  fallbackUsed?: boolean;   // True when Local was requested but Ollama was down
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export type Mode = 'local' | 'cloud';

interface ChatOptions {
  apiBaseUrl?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const useChatSocket = (options?: ChatOptions) => {
  const apiBaseUrl = options?.apiBaseUrl || API_BASE_URL;

  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [mode, setMode] = useState<Mode>('local');
  const [ollamaAvailable, setOllamaAvailable] = useState<boolean>(true);
  const hasInitialized = useRef<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // ── Health check ─────────────────────────────────────────────────────────────
  // On first load: auto-selects the best available mode.
  // On subsequent polls: keeps ollamaAvailable in sync for the LED.
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/health`);
        if (!res.ok) { setIsConnected(false); return; }

        const data: { status: string; ollama: boolean; openai: boolean } = await res.json();
        setIsConnected(true);
        setOllamaAvailable(data.ollama);

        // First poll: auto-select mode based on what's actually available
        if (!hasInitialized.current) {
          hasInitialized.current = true;
          if (!data.ollama) {
            // Ollama not reachable — start in Cloud mode automatically
            setMode('cloud');
          }
        } else {
          // Subsequent polls: if Ollama comes back online while in fallback, update LED
          // (user must manually switch back to Local; we don't force-switch)
        }
      } catch {
        setIsConnected(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  // ── Load conversation list on mount ─────────────────────────────────────────
  const refreshConversations = useCallback(async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/api/conversations`);
      if (res.ok) setConversations(await res.json());
    } catch {
      // Sidebar list failure is non-fatal
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // ── Start a brand new chat session ──────────────────────────────────────────
  const startNewChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  // ── Load a previous conversation from the sidebar ───────────────────────────
  const loadConversation = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/conversations/${id}`);
        if (!res.ok) return;

        const dbMessages: Array<{
          id: string;
          role: string;
          content: string;
          intent?: string;
          sentiment?: string;
        }> = await res.json();

        // Map DB rows → UI Message shape
        const loaded: Message[] = dbMessages.map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          insights:
            m.intent && m.sentiment
              ? { intent: m.intent, sentiment: m.sentiment }
              : undefined,
        }));

        setMessages(loaded);
        setConversationId(id);
      } catch {
        // If load fails, just leave current state untouched
      }
    },
    [apiBaseUrl]
  );

  // ── Delete a conversation ────────────────────────────────────────────────────
  const deleteConversation = useCallback(
    async (id: string) => {
      try {
        await fetch(`${apiBaseUrl}/api/conversations/${id}`, { method: 'DELETE' });
        // If we deleted the active conversation, reset to blank
        if (id === conversationId) startNewChat();
        await refreshConversations();
      } catch {
        // Non-fatal
      }
    },
    [apiBaseUrl, conversationId, startNewChat, refreshConversations]
  );

  // ── Send a message ───────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (userMessage: string): Promise<void> => {
      if (!isConnected || isGenerating) return;

      // Optimistically add the user message
      const userMsg: Message = {
        id: `${Date.now()}-user`,
        role: 'user',
        content: userMessage,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsGenerating(true);

      // Placeholder assistant bubble
      const assistantId = `${Date.now()}-ai`;
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: 'assistant', content: '...' },
      ]);

      abortControllerRef.current = new AbortController();

      try {
        // Build history snapshot (excludes placeholder and new user msg)
        const history = messages.map((m) => ({ role: m.role, content: m.content }));

        const res = await fetch(`${apiBaseUrl}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            history,
            conversation_id: conversationId,
            mode,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        const data: {
          reply: string;
          insights: Insights;
          conversation_id: string;
          fallback_used: boolean;
        } = await res.json();

        // If Ollama went down during this request, update availability state
        if (data.fallback_used) setOllamaAvailable(false);

        // Persist conversation ID returned from backend
        if (!conversationId) {
          setConversationId(data.conversation_id);
          await refreshConversations();
        }

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: data.reply,
                  insights: data.insights,
                  fallbackUsed: data.fallback_used,
                }
              : m
          )
        );
      } catch (error: any) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    error.name === 'AbortError'
                      ? '⏹️ Generation stopped.'
                      : `❌ Error: ${error.message}`,
                }
              : m
          )
        );
      } finally {
        setIsGenerating(false);
        abortControllerRef.current = null;
      }
    },
    [isConnected, isGenerating, messages, conversationId, apiBaseUrl, refreshConversations, mode]
  );

  const stopGeneration = useCallback((): void => {
    abortControllerRef.current?.abort();
    setIsGenerating(false);
  }, []);

  const generateBenchmarkReport = useCallback(async () => {
    if (!isConnected || isGenerating) return;

    setIsGenerating(true);
    const assistantId = `${Date.now()}-ai-benchmark`;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: 'assistant', content: 'Generating benchmark report...' },
    ]);

    try {
      const res = await fetch(`${apiBaseUrl}/api/documents/benchmark`);
      if (!res.ok) throw new Error('Failed to generate benchmark');
      const data = await res.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: data.report }
            : m
        )
      );
    } catch (error: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `❌ Error: ${error.message}` }
            : m
        )
      );
    } finally {
      setIsGenerating(false);
    }
  }, [isConnected, isGenerating, apiBaseUrl]);

  return {
    messages,
    conversations,
    conversationId,
    mode,
    setMode,
    ollamaAvailable,
    sendMessage,
    loadConversation,
    deleteConversation,
    startNewChat,
    refreshConversations,
    isConnected,
    isGenerating,
    stopGeneration,
    generateBenchmarkReport,
  };
};