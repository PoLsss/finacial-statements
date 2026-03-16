/**
 * Footer Component - Enhanced with cool blue theme
 */

import { Sparkles, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="border-t border-primary/10 bg-gradient-to-r from-background via-primary/5 to-background py-6 md:py-0">
      <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-r from-primary/20 to-accent/20 p-1.5 rounded-lg">
            <Sparkles className="h-3 w-3 text-primary" />
          </div>
          <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
            Financial Reports RAG Assistant &copy; {new Date().getFullYear()}
          </p>
        </div>
        <div className="flex items-center space-x-6 text-sm text-muted-foreground">
          <span className="flex items-center gap-2 bg-muted/50 px-3 py-1 rounded-full">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></span>
            Powered by Landing AI + OpenAI
          </span>
        </div>
      </div>
    </footer>
  );
}
