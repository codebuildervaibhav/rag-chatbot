// components/ChatView.tsx
//
// Scrollable message list with auto-scroll to bottom.
// Shows an empty state prompt when no messages are present.

import React, { useEffect, useRef } from 'react';
import Message from './Message';
import { Message as ChatMessage } from '../hooks/useChatSocket';

interface ChatViewProps {
  messages: ChatMessage[];
}

const ChatView: React.FC<ChatViewProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-8 select-none">
        <div className="text-5xl mb-4">💬</div>
        <h2 className="text-xl font-semibold text-gray-400 mb-2">Start a conversation</h2>
        <p className="text-sm text-center max-w-xs">
          Ask a question, share a problem, or just say hi.
          <br />
          Every response includes intent &amp; sentiment insights.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatView;