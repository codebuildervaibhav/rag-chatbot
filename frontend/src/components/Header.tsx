// components/Header.tsx
//
// Top bar — app title + mode-aware LED indicator + stop button.
//
// LED behaviour:
//   🟣 Purple → Strategy A (Raw Vector Search)
//   🟡 Amber  → Not used
//   🔵 Blue   → Strategy B (AI-Enhanced Retrieval)
//   🔴 Red    → Backend unreachable

import React from 'react';
import { Mode } from '../hooks/useChatSocket';

interface HeaderProps {
  isConnected: boolean;
  isGenerating: boolean;
  onStop: () => void;
  mode: Mode;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  isGenerating,
  onStop,
  mode,
}) => {
  const ledColor = !isConnected
    ? 'bg-red-400'
    : mode === 'local'
    ? 'bg-purple-400'
    : 'bg-blue-400';

  const ledGlow = !isConnected
    ? 'shadow-red-500/60'
    : mode === 'local'
    ? 'shadow-purple-500/60'
    : 'shadow-blue-500/60';

  const statusText = !isConnected
    ? 'Offline'
    : mode === 'local'
    ? 'Strategy A · Raw'
    : 'Strategy B · AI-Enhanced';

  const statusColor = !isConnected
    ? 'text-red-400'
    : mode === 'local'
    ? 'text-purple-400'
    : 'text-blue-400';

  const subtitle = !isConnected
    ? 'Backend offline'
    : mode === 'local'
    ? 'Raw Vector Embedding Search'
    : 'LLM Query Expansion + Vector Search';

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-gray-800 shadow-md border-b border-gray-700">
      <div>
        <h1 className="text-xl font-bold text-blue-400">Context-Aware Retrieval Engine</h1>
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