// components/ConversationSidebar.tsx
//
// Left sidebar showing the user's conversation history.
// Groups conversations by date: Today, Yesterday, Older.
// Supports: selecting a conversation, deleting one, starting a new chat.

import React, { useMemo } from 'react';
import { Conversation } from '../hooks/useChatSocket';

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
  isGenerating: boolean;
  onGenerateReport: () => void;
}

// ── Date grouping helper ────────────────────────────────────────────────────────

function getDateGroup(isoDate: string): 'Today' | 'Yesterday' | 'Older' {
  const date = new Date(isoDate);
  const now = new Date();

  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (isToday) return 'Today';

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate();

  if (isYesterday) return 'Yesterday';
  return 'Older';
}

// ── Sidebar Component ──────────────────────────────────────────────────────────

const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
  isGenerating,
  onGenerateReport,
}) => {
  const [docText, setDocText] = React.useState('');
  const [isIndexing, setIsIndexing] = React.useState(false);

  const handleIndex = async () => {
    if (!docText.trim()) return;
    setIsIndexing(true);
    try {
      const res = await fetch('http://localhost:8000/api/documents/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: docText }),
      });
      const data = await res.json();
      alert(`Indexed ${data.chunks_indexed} chunks successfully!`);
      setDocText('');
    } catch (e) {
      alert('Failed to index document.');
      console.error(e);
    } finally {
      setIsIndexing(false);
    }
  };

  // Group conversations by date label
  const grouped = useMemo(() => {
    const groups: Record<string, Conversation[]> = {
      Today: [],
      Yesterday: [],
      Older: [],
    };
    for (const conv of conversations) {
      groups[getDateGroup(conv.updated_at)].push(conv);
    }
    return groups;
  }, [conversations]);

  const groupOrder = ['Today', 'Yesterday', 'Older'] as const;

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-gray-850 border-r border-gray-700 h-full overflow-hidden"
           style={{ backgroundColor: '#111827' }}>

      {/* New Chat button */}
      <div className="p-3 border-b border-gray-700">
        <button
          id="new-chat-button"
          onClick={onNewChat}
          disabled={isGenerating}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white transition-colors text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span className="text-lg leading-none">✏️</span>
          New Chat
        </button>
        
        <button
          onClick={onGenerateReport}
          disabled={isGenerating}
          className="w-full mt-2 flex items-center gap-2 px-3 py-2.5 rounded-lg border border-purple-500/50 bg-purple-900/20 text-purple-300 hover:bg-purple-900/40 hover:text-purple-200 transition-colors text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <span className="text-lg leading-none">📊</span>
          Run Benchmark
        </button>
      </div>

      {/* Document Ingestion Area */}
      <div className="p-3 border-b border-gray-700 flex flex-col gap-2">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Context Document
        </div>
        <textarea
          rows={3}
          value={docText}
          onChange={(e) => setDocText(e.target.value)}
          placeholder="Paste text here to index into the vector DB..."
          className="w-full p-2 text-xs rounded-md bg-gray-700 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        />
        <button
          onClick={handleIndex}
          disabled={isIndexing || !docText.trim()}
          className="w-full px-2 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isIndexing ? 'Indexing...' : 'Index Document'}
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <div className="px-4 py-6 text-center text-gray-500 text-xs">
            No conversations yet.
            <br />
            Start chatting!
          </div>
        ) : (
          groupOrder.map((group) => {
            const items = grouped[group];
            if (items.length === 0) return null;
            return (
              <div key={group} className="mb-2">
                {/* Date group label */}
                <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  {group}
                </div>

                {/* Conversation items */}
                {items.map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <div
                      key={conv.id}
                      className={`group relative mx-2 mb-0.5 rounded-lg flex items-center ${
                        isActive
                          ? 'bg-gray-700 text-white'
                          : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                      }`}
                    >
                      {/* Select conversation */}
                      <button
                        onClick={() => onSelectConversation(conv.id)}
                        className="flex-1 text-left px-3 py-2.5 text-sm truncate"
                        title={conv.title}
                      >
                        {conv.title}
                      </button>

                      {/* Delete button — visible on hover */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(conv.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity pr-2 text-gray-500 hover:text-red-400 text-xs flex-shrink-0"
                        title="Delete conversation"
                      >
                        🗑
                      </button>
                    </div>
                  );
                })}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-700">
        <p className="text-xs text-gray-600 text-center">
          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''} saved
        </p>
      </div>
    </aside>
  );
};

export default ConversationSidebar;
