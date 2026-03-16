/**
 * ChatContainer Component - 3-panel layout: history (left) | chat (center) | context + detail (right)
 */

'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ContextPanel } from './ContextPanel';
import { ThinkingIndicator } from './ThinkingIndicator';
import { useChat } from '@/hooks/useChat';
import type { Conversation } from '@/stores/chatStore';
import type { Chunk } from '@/types/api';
import {
  MessageSquarePlus,
  Trash2,
  MessagesSquare,
  Clock,
} from 'lucide-react';

function formatDate(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 0) return 'Hôm nay';
  if (diffDays === 1) return 'Hôm qua';
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
}

export function ChatContainer() {
  const {
    messages,
    chunks,
    routingMetadata,
    isLoading,
    error,
    thinking,
    conversations,
    sendMessage,
    startNewChat,
    loadConversation,
    deleteConversation,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [selectedChunk, setSelectedChunk] = useState<Chunk | null>(null);
  const [rightWidth, setRightWidth] = useState(460);
  const isDragging = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleDividerMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newRight = rect.right - ev.clientX;
      setRightWidth(Math.max(300, Math.min(800, newRight)));
    };
    const onMouseUp = () => {
      isDragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, []);

  return (
    <div ref={containerRef} className="flex h-[calc(100vh-64px)] overflow-hidden bg-linear-to-b from-background to-slate-50/50 dark:to-slate-900/20">

      {/* LEFT SIDEBAR: Chat history */}
      <aside className="w-56 shrink-0 border-r bg-slate-50 dark:bg-slate-900/60 flex flex-col overflow-hidden">
        <div className="px-3 py-2.5 border-b bg-slate-100 dark:bg-slate-900 flex items-center gap-2">
          <Clock className="h-3.5 w-3.5 text-blue-500" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Lịch sử</span>
        </div>
        <div className="px-2.5 py-2 border-b">
          <Button
            variant="outline"
            size="sm"
            className="w-full h-8 gap-1.5 text-xs border-blue-200 dark:border-blue-800 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400 font-medium"
            onClick={startNewChat}
          >
            <MessageSquarePlus className="h-3.5 w-3.5" />
            Hội thoại mới
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-8 px-3">Chưa có lịch sử hội thoại</p>
          ) : (
            <div className="px-2 py-2 space-y-0.5">
              {conversations.map((conv: Conversation) => (
                <div
                  key={conv.id}
                  className="group flex items-start gap-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 px-2 py-2 transition-colors cursor-pointer border border-transparent hover:border-blue-100 dark:hover:border-blue-900"
                  onClick={() => loadConversation(conv.id)}
                >
                  <MessagesSquare className="h-3.5 w-3.5 text-blue-400 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium leading-tight line-clamp-2 text-slate-700 dark:text-slate-300">{conv.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{formatDate(conv.createdAt)}</p>
                  </div>
                  <button
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-500 transition-all shrink-0 mt-0.5"
                    onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                    title="Xóa"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* CENTER: Chat area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-2.5 border-b bg-background/90 backdrop-blur-sm shrink-0">
          <MessagesSquare className="h-4 w-4 text-blue-500" />
          <h1 className="text-base font-bold text-slate-800 dark:text-slate-100">Trợ lý tài chính AI</h1>
          <span className="text-xs text-muted-foreground hidden sm:block">· Hỏi đáp về báo cáo tài chính</span>
        </div>

        <div className="flex-1 overflow-y-auto px-4">
          <div className="py-6 space-y-4 max-w-3xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center py-16">
                <p className="text-5xl mb-4">🏢</p>
                <p className="text-xl font-semibold text-slate-700 dark:text-slate-200">Xin chào! Tôi có thể giúp gì?</p>
                <p className="text-sm mt-2 text-muted-foreground">Đặt câu hỏi về báo cáo tài chính của công ty</p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center">
                  {['Doanh thu quý 3?', 'Tỷ lệ nợ trên vốn?', 'Lợi nhuận ròng?'].map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="text-xs px-3 py-1.5 rounded-full border border-blue-200 dark:border-blue-800 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-blue-600 dark:text-blue-400 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <MessageBubble key={index} message={message} />
              ))
            )}
            {(thinking.isThinking || thinking.steps.length > 0) && isLoading && (
              <ThinkingIndicator thinking={thinking} />
            )}
            {error && (
              <div className="bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm border border-red-200 dark:border-red-800">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="px-4 py-3 border-t bg-background/90 backdrop-blur-sm shrink-0">
          <div className="max-w-3xl mx-auto">
            <ChatInput onSend={sendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>

      {/* DRAGGABLE DIVIDER */}
      <div
        onMouseDown={handleDividerMouseDown}
        className="w-1.5 shrink-0 cursor-col-resize hover:bg-blue-400 active:bg-blue-500 bg-slate-200 dark:bg-slate-700 transition-colors duration-150 group relative"
        title="Kéo để thay đổi kích thước"
      >
        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-0.5 group-hover:bg-blue-400" />
      </div>

      {/* RIGHT: Context panel */}
      <div style={{ width: rightWidth }} className="shrink-0 overflow-hidden flex flex-col bg-slate-50 dark:bg-slate-900/40">
        <ContextPanel
          chunks={chunks}
          routingMetadata={routingMetadata}
          onChunkSelect={setSelectedChunk}
          selectedChunk={selectedChunk}
        />
      </div>
    </div>
  );
}
