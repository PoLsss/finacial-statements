/**
 * MessageList Component - List of chat messages
 */

'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from './MessageBubble';
import type { ChatMessage } from '@/types/api';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <ScrollArea className="h-[500px] pr-4" ref={scrollRef}>
      <div className="space-y-4 py-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p className="text-4xl mb-4">💬</p>
            <p className="text-lg font-medium">Start a conversation</p>
            <p className="text-sm">Ask anything about your financial reports!</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3 max-w-[80%]">
              <div className="flex items-center gap-2">
                <span className="text-lg">🤖</span>
                <span className="text-xs font-medium opacity-70">Assistant</span>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <span className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
