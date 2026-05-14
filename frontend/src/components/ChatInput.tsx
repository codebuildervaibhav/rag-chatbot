// components/ChatInput.tsx
//
// Multi-line text input with mode toggle.
//
// Layout (bottom bar):
//   [ textarea                                              ]
//   [ 🐾 Local ⟷ ☁️ Cloud ]              [ Send ▶ ]
//
// - Enter → send, Shift+Enter → newline
// - Pill toggle switches between Local (Murphy) and Cloud (Casper) mode
// - Toggle is disabled while a response is generating

import React, { Dispatch, SetStateAction } from 'react';
import { Mode } from '../hooks/useChatSocket';

interface ChatInputProps {
  input: string;
  setInput: Dispatch<SetStateAction<string>>;
  onSendMessage: () => void;
  isGenerating: boolean;
  mode: Mode;
  onModeChange: (mode: Mode) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  onSendMessage,
  isGenerating,
  mode,
  onModeChange,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isGenerating) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div className="p-4 bg-gray-800 border-t border-gray-700 flex flex-col gap-2">
      {/* Textarea */}
      <textarea
        id="chat-input"
        rows={2}
        className="w-full p-3 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none leading-relaxed"
        placeholder={
          isGenerating
            ? 'Generating response…'
            : 'Type a message… (Enter to send, Shift+Enter for new line)'
        }
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isGenerating}
      />

      {/* Bottom row: mode toggle + send button */}
      <div className="flex items-center justify-between">

        {/* Mode pill toggle */}
        <div
          className="flex items-center bg-gray-700 rounded-full p-0.5 gap-0.5"
          role="group"
          aria-label="AI mode selector"
        >
          <button
            id="mode-local-btn"
            onClick={() => onModeChange('local')}
            disabled={isGenerating}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'local'
                ? 'bg-green-600 text-white shadow-md shadow-green-900/50'
                : 'text-gray-400 hover:text-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            🐾 <span>Local</span>
          </button>

          <button
            id="mode-cloud-btn"
            onClick={() => onModeChange('cloud')}
            disabled={isGenerating}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              mode === 'cloud'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-900/50'
                : 'text-gray-400 hover:text-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            ☁️ <span>Cloud</span>
          </button>
        </div>

        {/* Mode label — small hint */}
        <span className="text-xs text-gray-500">
          {mode === 'local' ? 'Murphy · Ollama + NLP' : 'Casper · GPT-4o-mini'}
        </span>

        {/* Send button */}
        <button
          id="send-button"
          onClick={onSendMessage}
          disabled={!input.trim() || isGenerating}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInput;