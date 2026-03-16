/**
 * MessageBubble Component - Individual chat message with enhanced styling
 */

'use client';

import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '@/types/api';
import { User, Bot } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      <div
        className={`
          max-w-[80%] rounded-2xl px-4 py-3 shadow-sm
          ${
            isUser
              ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground shadow-primary/20'
              : 'bg-gradient-to-br from-muted to-muted/80 border border-primary/5'
          }
        `}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className={`
            p-1.5 rounded-lg
            ${isUser 
              ? 'bg-white/20' 
              : 'bg-gradient-to-br from-accent/20 to-primary/20'
            }
          `}>
            {isUser ? (
              <User className="h-3.5 w-3.5" />
            ) : (
              <Bot className="h-3.5 w-3.5 text-primary" />
            )}
          </div>
          <span className="text-xs font-medium opacity-70">
            {isUser ? 'You' : 'Financial Expert AI'}
          </span>
        </div>
        
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-headings:text-primary prose-strong:text-primary prose-code:bg-primary/10 prose-code:text-primary prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
