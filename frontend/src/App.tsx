// App.tsx — root component, assembles the full layout.

import { useState } from 'react';
import { Header } from './components/Header';
import ChatView from './components/ChatView';
import ChatInput from './components/ChatInput';
import ConversationSidebar from './components/ConversationSidebar';
import { useChatSocket } from './hooks/useChatSocket';

function App() {
  const {
    messages,
    conversations,
    conversationId,
    mode,
    setMode,
    //ollamaAvailable,
    sendMessage,
    loadConversation,
    deleteConversation,
    startNewChat,
    isConnected,
    isGenerating,
    stopGeneration,
    generateBenchmarkReport,
  } = useChatSocket();

  const [input, setInput] = useState<string>('');

  const handleSendMessage = () => {
    if (input.trim() && !isGenerating) {
      sendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header — receives mode so the LED reflects local vs cloud */}
      <Header
        isConnected={isConnected}
        isGenerating={isGenerating}
        onStop={stopGeneration}
        mode={mode}
      />

      {/* Main content: sidebar + chat */}
      <div className="flex flex-1 overflow-hidden">
        {/* Conversation history sidebar */}
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={conversationId}
          onSelectConversation={loadConversation}
          onDeleteConversation={deleteConversation}
          onNewChat={startNewChat}
          isGenerating={isGenerating}
          onGenerateReport={generateBenchmarkReport}
        />

        {/* Chat area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <ChatView messages={messages} />
          <ChatInput
            input={input}
            setInput={setInput}
            onSendMessage={handleSendMessage}
            isGenerating={isGenerating}
            mode={mode}
            onModeChange={setMode}
          />
        </div>
      </div>
    </div>
  );
}

export default App;