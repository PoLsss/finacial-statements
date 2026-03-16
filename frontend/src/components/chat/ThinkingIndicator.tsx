/**
 * ThinkingIndicator Component - Shows thinking process steps
 */

'use client';

import { Card, CardContent } from '@/components/ui/card';
import type { ThinkingState } from '@/stores/chatStore';

interface ThinkingIndicatorProps {
  thinking: ThinkingState;
}

export function ThinkingIndicator({ thinking }: ThinkingIndicatorProps) {
  if (!thinking.isThinking && thinking.steps.length === 0) return null;

  return (
    <Card className="border-primary/30 bg-gradient-to-r from-primary/5 to-primary/10 animate-pulse">
      <CardContent className="py-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
          <span className="text-sm font-medium text-primary">Processing your question...</span>
        </div>
        
        <div className="space-y-2 pl-6">
          {thinking.steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center gap-2 text-sm transition-all duration-300 ${
                index === thinking.steps.length - 1 && thinking.isThinking
                  ? 'text-primary font-medium'
                  : 'text-muted-foreground'
              }`}
            >
              <span className={`w-4 h-4 flex items-center justify-center rounded-full text-xs ${
                index === thinking.steps.length - 1 && thinking.isThinking
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-green-500 text-white'
              }`}>
                {index === thinking.steps.length - 1 && thinking.isThinking ? '→' : '✓'}
              </span>
              <span>{step}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
