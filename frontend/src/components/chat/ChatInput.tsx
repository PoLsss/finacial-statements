/**
 * ChatInput Component - Message input box with enhanced styling
 */

'use client';

import { useState, KeyboardEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Sparkles } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled,
  placeholder = 'Đặt câu hỏi về báo cáo tài chính...',
}: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative">
      <div className="flex gap-3 p-2 rounded-2xl bg-gradient-to-r from-muted/50 to-muted/30 border border-primary/10 shadow-lg shadow-primary/5">
        <div className="flex-1 relative">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="min-h-[60px] resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-muted-foreground/50"
            rows={2}
          />
        </div>
        <div className="flex flex-col justify-end pb-1">
          <Button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="px-4 py-2 h-10 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25 rounded-xl"
          >
            <Send className="h-4 w-4 mr-2" />
            Gửi
          </Button>
        </div>
      </div>
      <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground/60 px-2">
        <Sparkles className="h-3 w-3" />
        <span>Enter để gửi, Shift+Enter xuống dòng</span>
      </div>
    </div>
  );
}
