// components/Message.tsx
//
// Renders a single chat message bubble.
// - User messages: right-aligned, blue
// - Assistant messages: left-aligned, dark gray
//
// For assistant messages, shows an InsightsBadge below the content
// displaying the intent and sentiment extracted from the user's input.

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import dark from 'react-syntax-highlighter/dist/esm/styles/prism/dark';
import { Message as ChatMessage, Insights } from '../hooks/useChatSocket';

interface MessageProps {
  message: ChatMessage;
}

// ── Insight Badge Configuration ────────────────────────────────────────────────

const SENTIMENT_CONFIG: Record<string, { label: string; emoji: string; classes: string }> = {
  positive: {
    label: 'Positive',
    emoji: '😊',
    classes: 'bg-green-900/40 border-green-600 text-green-300',
  },
  neutral: {
    label: 'Neutral',
    emoji: '😐',
    classes: 'bg-yellow-900/40 border-yellow-600 text-yellow-300',
  },
  negative: {
    label: 'Negative',
    emoji: '😞',
    classes: 'bg-red-900/40 border-red-600 text-red-300',
  },
};

const INTENT_CONFIG: Record<string, { label: string; emoji: string }> = {
  complaint: { label: 'Complaint', emoji: '⚠️' },
  query:     { label: 'Query',     emoji: '❓' },
  request:   { label: 'Request',   emoji: '📋' },
  greeting:  { label: 'Greeting',  emoji: '👋' },
  general:   { label: 'General',   emoji: '💬' },
};

// ── Insights Badge ─────────────────────────────────────────────────────────────

const InsightsBadge: React.FC<{ insights: Insights }> = ({ insights }) => {
  const sentiment = SENTIMENT_CONFIG[insights.sentiment] ?? SENTIMENT_CONFIG.neutral;
  const intent    = INTENT_CONFIG[insights.intent]       ?? INTENT_CONFIG.general;

  return (
    <div className="mt-3 pt-2 border-t border-gray-500/50">
      <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
        Insights
      </span>
      <div className="flex items-center gap-2 flex-wrap mt-1.5">
        {/* Sentiment chip — color-coded green/yellow/red */}
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${sentiment.classes}`}
        >
          {sentiment.emoji} {sentiment.label}
        </span>

        {/* Intent chip — neutral gray */}
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gray-500 bg-gray-600/40 text-gray-200 text-xs font-semibold">
          {intent.emoji} {intent.label}
        </span>
      </div>
    </div>
  );
};

// ── Message Component ──────────────────────────────────────────────────────────

const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3xl p-4 rounded-2xl shadow-md ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm'
            : 'bg-gray-700 text-gray-100 rounded-bl-sm'
        }`}
      >
        {/* Message content with markdown + syntax highlighting */}
        <ReactMarkdown
          children={message.content}
          components={{
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  children={String(children).replace(/\n$/, '')}
                  style={dark}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                />
              ) : (
                <code
                  className={`${className} bg-black/20 px-1 py-0.5 rounded text-sm font-mono`}
                  {...props}
                >
                  {children}
                </code>
              );
            },
          }}
        />

        {/* Insights badge — only on assistant messages that have insights data */}
        {!isUser && message.insights && (
          <InsightsBadge insights={message.insights} />
        )}

        {/* Fallback note — shown when Local was selected but Ollama was unavailable */}
        {!isUser && message.fallbackUsed && (
          <p className="mt-2 text-xs text-amber-400/70 italic">
            ☁️ served by Casper — Murphy unavailable
          </p>
        )}
      </div>
    </div>
  );
};

export default Message;