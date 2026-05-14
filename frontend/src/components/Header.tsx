// components/Header.tsx
//
// Top bar — app title + mode-aware LED indicator + stop button.
//
// LED behaviour:
//   🟢 Green  → Local mode, Ollama UP (Murphy serving)
//   🟡 Amber  → Local mode, Ollama DOWN (Casper serving as fallback)
//   🔵 Blue   → Cloud mode active (Casper/GPT-4o-mini)
//   🔴 Red    → Backend unreachable

import React from 'react';
import { Mode } from '../hooks/useChatSocket';

interface HeaderProps {
  isConnected: boolean;
  isGenerating: boolean;
  onStop: () => void;
  mode: Mode;
  ollamaAvailable: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  isGenerating,
  onStop,
  mode,
  ollamaAvailable,
}) => {
  // Compute LED state
  const isFallback = mode === 'local' && !ollamaAvailable;

  const ledColor = !isConnected
    ? 'bg-red-400'
    : isFallback
    ? 'bg-amber-400'
    : mode === 'local'
    ? 'bg-green-400'
    : 'bg-blue-400';

  const ledGlow = !isConnected
    ? 'shadow-red-500/60'
    : isFallback
    ? 'shadow-amber-500/60'
    : mode === 'local'
    ? 'shadow-green-500/60'
    : 'shadow-blue-500/60';

  const statusText = !isConnected
    ? 'Offline'
    : isFallback
    ? 'Casper · Fallback'
    : mode === 'local'
    ? 'Murphy · Local'
    : 'Casper · Cloud';

  const statusColor = !isConnected
    ? 'text-red-400'
    : isFallback
    ? 'text-amber-400'
    : mode === 'local'
    ? 'text-green-400'
    : 'text-blue-400';

  const subtitle = !isConnected
    ? 'Backend offline'
    : isFallback
    ? 'Ollama unavailable · using GPT-4o-mini'
    : mode === 'local'
    ? 'Ollama/Gemma · NLTK + VADER'
    : 'GPT-4o-mini · OpenAI';

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-gray-800 shadow-md border-b border-gray-700">
      <div>
        <h1 className="text-xl font-bold text-blue-400">AI Chatbot</h1>
        <p className="text-xs text-gray-500 transition-all duration-300">{subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Mode-aware LED indicator */}
        <div className="flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full shadow-[0_0_6px_2px] ${ledColor} ${ledGlow} transition-all duration-300`}
          />
          <span className={`text-sm font-medium transition-colors duration-300 ${statusColor}`}>
            {statusText}
          </span>
        </div>

        {/* Stop button — only shown while generating */}
        {isGenerating && (
          <button
            id="stop-button"
            onClick={onStop}
            className="px-4 py-1.5 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 transition-colors"
          >
            ⏹ Stop
          </button>
        )}
      </div>
    </header>
  );
};