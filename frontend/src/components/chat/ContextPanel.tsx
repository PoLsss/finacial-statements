/**
 * ContextPanel Component - Shows retrieved chunks list. Click a chunk to see full-panel detail.
 */

'use client';

import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { ChevronRight, FileText, BookOpen, Cpu, ArrowLeft } from 'lucide-react';
import type { Chunk, RoutingMetadata } from '@/types/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

interface ContextPanelProps {
  chunks: Chunk[];
  routingMetadata: RoutingMetadata | null;
  onChunkSelect?: (chunk: Chunk | null) => void;
  selectedChunk?: Chunk | null;
}

function prepareContent(raw: string): string {
  let content = raw || '';
  content = content.replace(/<a\s+id=['"][^'"]+['"]\s*><\/a>/gi, '');
  content = content.replace(/\s+id=['"][^'"]+['"]/gi, '');
  try {
    const parsed = JSON.parse(content);
    if (typeof parsed === 'object' && parsed !== null) {
      content = '### Thông tin chi tiết\n' + Object.entries(parsed)
        .map(([key, value]) => `- **${key}**: ${value}`)
        .join('\n');
    }
  } catch {
    // plain text / markdown, keep as-is
  }
  return content;
}

function ChunkDetailView({ chunk, index, onBack }: { chunk: Chunk; index: number; onBack: () => void }) {
  const metadata = chunk.metadata as Record<string, unknown> || {};
  const pageIndex = metadata.page_index as number | undefined;
  const source = metadata.source as string | undefined;
  const sourceName = source ? source.split('/').pop()?.replace(/\.(pdf|md|txt)$/i, '') : undefined;
  const displayContent = prepareContent(chunk.page_content);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b bg-blue-50 dark:bg-blue-950/40 shrink-0">
        <button
          onClick={onBack}
          className="p-1 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors shrink-0"
          title="Quay lại danh sách"
        >
          <ArrowLeft className="h-4 w-4 text-blue-600" />
        </button>
        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 rounded px-1.5 py-0.5 font-mono shrink-0">
          #{index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            {pageIndex !== undefined && (
              <span className="inline-flex items-center gap-0.5 text-xs font-bold text-white bg-blue-500 rounded-md px-2 py-0.5">
                <BookOpen className="h-3 w-3 mr-0.5" />Trang {pageIndex + 1}
              </span>
            )}
            {sourceName && (
              <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[160px]" title={sourceName}>
                <FileText className="h-3 w-3 shrink-0" />
                <span className="truncate">{sourceName}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="prose prose-sm dark:prose-invert max-w-none leading-relaxed text-sm text-foreground/90">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-3 border rounded-lg border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-sm border-collapse" {...props} />
                </div>
              ),
              th: ({ node, ...props }) => <th className="bg-slate-50 dark:bg-slate-900 font-semibold p-2.5 border-b border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 whitespace-nowrap" {...props} />,
              td: ({ node, ...props }) => <td className="p-2.5 border-b border-slate-200/50 dark:border-slate-800/50 align-top" {...props} />,
              h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-2 text-slate-900 dark:text-slate-100" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-3 mb-2 text-slate-800 dark:text-slate-200" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-base font-semibold mt-3 mb-1 text-slate-800 dark:text-slate-200" {...props} />,
              p: ({ node, ...props }) => <p className="mb-2 leading-relaxed" {...props} />,
            }}
          >
            {displayContent}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

function ChunkListItem({ chunk, index, onSelect }: { chunk: Chunk; index: number; onSelect: (chunk: Chunk) => void }) {
  const metadata = chunk.metadata as Record<string, unknown> || {};
  const pageIndex = metadata.page_index as number | undefined;
  const source = metadata.source as string | undefined;
  const sourceName = source ? source.split('/').pop()?.replace(/\.(pdf|md|txt)$/i, '') : undefined;
  const preview = prepareContent(chunk.page_content).replace(/[#*`>_~]/g, '').slice(0, 120).trim();

  return (
    <button
      type="button"
      className="w-full text-left border rounded-lg overflow-hidden transition-all duration-200 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 hover:shadow-sm bg-white dark:bg-slate-900/30"
      onClick={() => onSelect(chunk)}
    >
      <div className="flex items-start gap-2 px-3 py-2.5">
        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 bg-blue-500/10 rounded px-1.5 py-0.5 shrink-0 font-mono mt-0.5">
          #{index + 1}
        </span>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            {pageIndex !== undefined && (
              <div className="flex items-center gap-1">
                <BookOpen className="h-3 w-3 text-blue-500 shrink-0" />
                <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">Trang {pageIndex + 1}</span>
              </div>
            )}
            {sourceName && (
              <div className="flex items-center gap-1">
                <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="text-[10px] text-muted-foreground truncate max-w-[140px]" title={sourceName}>{sourceName}</span>
              </div>
            )}
          </div>
          {preview && (
            <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">{preview}…</p>
          )}
        </div>
        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground mt-0.5" />
      </div>
    </button>
  );
}

export function ContextPanel({ chunks, routingMetadata, onChunkSelect, selectedChunk }: ContextPanelProps) {
  const selectedIndex = selectedChunk ? chunks.indexOf(selectedChunk) : -1;

  const handleSelect = (chunk: Chunk) => {
    if (onChunkSelect) onChunkSelect(chunk);
  };

  const handleBack = () => {
    if (onChunkSelect) onChunkSelect(null);
  };

  // DETAIL VIEW: fills entire panel
  if (selectedChunk && selectedIndex !== -1) {
    return <ChunkDetailView chunk={selectedChunk} index={selectedIndex} onBack={handleBack} />;
  }

  // LIST VIEW
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Routing info */}
      {routingMetadata && (
        <div className="px-3 py-2 border-b bg-muted/20 shrink-0">
          <div className="flex items-center gap-2 mb-1.5">
            <Cpu className="h-3.5 w-3.5 text-violet-500" />
            <span className="text-xs font-medium">Phân tích câu hỏi</span>
            <Badge variant={routingMetadata.routing_decision === 'agent' ? 'default' : 'secondary'} className="text-[10px] px-1.5 py-0 h-4 ml-auto">
              {routingMetadata.routing_decision === 'agent' ? 'Agent RAG' : 'Simple RAG'}
            </Badge>
          </div>
          <div className="flex gap-2 text-[10px] text-muted-foreground flex-wrap">
            <span>Độ phức tạp: <b className="text-foreground/70">{routingMetadata.complexity_level}</b></span>
            <span>Điểm: <b className="font-mono text-foreground/70">{routingMetadata.complexity_score.toFixed(2)}</b></span>
          </div>
        </div>
      )}

      {/* Chunks header */}
      <div className="px-3 py-2 border-b flex items-center gap-2 shrink-0 bg-background">
        <BookOpen className="h-3.5 w-3.5 text-blue-500" />
        <span className="text-xs font-semibold">Ngữ cảnh truy xuất</span>
        {chunks.length > 0 && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 ml-auto">{chunks.length} đoạn</Badge>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="px-2 py-2 space-y-1.5">
          {chunks.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-8">
              Chưa có ngữ cảnh nào được truy xuất
            </p>
          ) : (
            chunks.map((chunk, index) => (
              <ChunkListItem key={index} chunk={chunk} index={index} onSelect={handleSelect} />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

