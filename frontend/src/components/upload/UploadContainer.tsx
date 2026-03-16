/**
 * UploadContainer Component - Redesigned 1-screen layout with sidebar
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { DropZone } from './DropZone';
import { useUpload } from '@/hooks/useUpload';
import { getCompanies } from '@/lib/api';
import type { CompanyInfo } from '@/types/api';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  Loader2,
  Database,
  BookOpen,
  RotateCcw,
  Settings2,
  RefreshCw,
  Clock,
  Layers,
  Trash2,
} from 'lucide-react';

interface ProcessStep {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'active' | 'done' | 'error';
}

const PROCESS_STEPS: Omit<ProcessStep, 'status'>[] = [
  { id: 'upload',  label: 'Tải file lên',            description: 'Đang gửi file PDF lên server...' },
  { id: 'parse',   label: 'Phân tích cấu trúc PDF',  description: 'LandingAI đang nhận dạng bố cục...' },
  { id: 'chunk',   label: 'Chia nhỏ nội dung',       description: 'Tách tài liệu thành các đoạn văn bản...' },
  { id: 'embed',   label: 'Tạo Embedding',            description: 'Vector hóa các đoạn văn bản...' },
  { id: 'extract', label: 'Trích xuất dữ liệu',      description: 'Trích xuất chỉ số tài chính...' },
  { id: 'ratios',  label: 'Tính tỷ số tài chính',    description: 'Tính toán và lưu các tỷ số...' },
  { id: 'done',    label: 'Hoàn thành',              description: 'Tài liệu đã sẵn sàng sử dụng.' },
];

function buildSteps(progressVal: number, isError: boolean): ProcessStep[] {
  return PROCESS_STEPS.map((s, i) => {
    const threshold     = Math.round(((i + 1) / PROCESS_STEPS.length) * 100);
    const prevThreshold = Math.round((i / PROCESS_STEPS.length) * 100);
    let status: ProcessStep['status'] = 'pending';
    if (isError) {
      status = progressVal >= prevThreshold ? (progressVal >= threshold ? 'done' : 'error') : 'pending';
    } else if (progressVal >= threshold) {
      status = 'done';
    } else if (progressVal >= prevThreshold) {
      status = 'active';
    }
    return { ...s, status };
  });
}

interface SidebarToast {
  type: 'success' | 'error';
  message: string;
}

export function UploadContainer() {
  const { status, progress, result, error, file, selectFile, upload, reset } = useUpload();
  const [resetDatabase, setResetDatabase] = useState(false);
  const [documents, setDocuments]         = useState<CompanyInfo[]>([]);
  const [docsLoading, setDocsLoading]     = useState(false);
  const [confirmId, setConfirmId]         = useState<string | null>(null);
  const [deletingId, setDeletingId]       = useState<string | null>(null);
  const [toast, setToast]                 = useState<SidebarToast | null>(null);

  const isProcessing = status === 'uploading' || status === 'processing';
  const isDone       = status === 'success' || status === 'error';

  const showToast = useCallback((t: SidebarToast) => {
    setToast(t);
    setTimeout(() => setToast(null), 3500);
  }, []);

  const loadDocuments = useCallback(() => {
    setDocsLoading(true);
    getCompanies()
      .then((res) => { if (res.success && res.data) setDocuments(res.data); })
      .catch(() => {})
      .finally(() => setDocsLoading(false));
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  useEffect(() => {
    if (status === 'success') loadDocuments();
  }, [status, loadDocuments]);

  const handleConfirmDelete = async (source: string) => {
    setConfirmId(null);
    setDeletingId(source);
    try {
      const { deleteDocument } = await import('@/lib/api');
      const res = await deleteDocument(source);
      if (res.success) {
        setDocuments((prev) => prev.filter((d) => d.source !== source));
        showToast({
          type: 'success',
          message: `Đã xóa "${source}" (${res.deleted_chunks ?? 0} chunks, ${res.deleted_embeddings ?? 0} embeddings)`,
        });
      } else {
        showToast({ type: 'error', message: res.message || 'Xóa thất bại' });
      }
    } catch (e: unknown) {
      showToast({ type: 'error', message: e instanceof Error ? e.message : 'Lỗi không xác định' });
    } finally {
      setDeletingId(null);
    }
  };

  const steps = buildSteps(progress, status === 'error');

  return (
    <div className="flex h-[calc(100vh-64px)] gap-0 overflow-hidden">

      {/* ── LEFT SIDEBAR ── */}
      <aside className="w-80 shrink-0 border-r bg-muted/20 flex flex-col">

        {/* Sidebar header */}
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-teal-500" />
            <span className="text-sm font-semibold">Kho tài liệu</span>
          </div>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={loadDocuments} disabled={docsLoading}>
            <RefreshCw className={`h-3.5 w-3.5 ${docsLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Toast notification */}
        {toast && (
          <div
            className={`mx-3 mt-2 px-3 py-2 rounded-lg text-xs flex items-start gap-2 font-medium shadow-sm border
              ${toast.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
                : 'bg-red-500/10 border-red-500/30 text-red-600 dark:text-red-400'
              }`}
            aria-live="polite"
          >
            {toast.type === 'success'
              ? <CheckCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              : <XCircle    className="h-3.5 w-3.5 mt-0.5 shrink-0" />}
            <span className="leading-tight break-words min-w-0">{toast.message}</span>
          </div>
        )}

        {/* Stats pill */}
        <div className="px-4 py-3 border-b">
          <div className="rounded-lg bg-teal-500/10 border border-teal-500/20 px-3 py-2 flex items-center gap-3">
            <div className="text-2xl font-bold text-teal-600 dark:text-teal-400 leading-none">
              {documents.length}
            </div>
            <div>
              <div className="text-xs font-medium">Tài liệu đã tải</div>
              <div className="text-[10px] text-muted-foreground">trong hệ thống</div>
            </div>
          </div>
        </div>

        {/* List label */}
        <div className="flex items-center gap-1.5 px-4 py-2 border-b">
          <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Danh sách</span>
        </div>

        {/* Document cards — plain div so content respects sidebar width */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="px-2 py-2 space-y-1">
            {docsLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : documents.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-6">Chưa có tài liệu nào</p>
            ) : (
              documents.map((doc) => {
                const isConfirming = confirmId === doc.source;
                const isDeleting   = deletingId === doc.source;

                return (
                  <div
                    key={doc.source}
                    className={[
                      'group rounded-md border bg-background/60 px-2 py-2 overflow-hidden',
                      'transition-all duration-200',
                      isConfirming
                        ? 'border-red-400/60 bg-red-50/60 dark:bg-red-950/20 shadow-sm'
                        : 'hover:bg-background hover:border-border/70 hover:shadow-sm',
                      isDeleting ? 'opacity-50 pointer-events-none' : '',
                    ].join(' ')}
                  >
                    {/* ── Main row: icon + text + delete button ── */}
                    <div className="flex items-center gap-1.5 w-full min-w-0">
                      {/* Leading icon */}
                      {isDeleting ? (
                        <Loader2 className="h-3.5 w-3.5 text-red-500 shrink-0 animate-spin" />
                      ) : (
                        <FileText className={`h-3.5 w-3.5 shrink-0 transition-colors ${isConfirming ? 'text-red-500' : 'text-teal-500'}`} />
                      )}

                      {/* Text — takes all remaining space */}
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium truncate leading-tight" title={doc.company || doc.source}>
                          {doc.company || doc.source}
                        </p>
                        <div className="flex items-center gap-1 mt-0.5">
                          <Badge variant="outline" className="text-[9px] px-1 py-0 h-4">{doc.period}</Badge>
                          <span className="text-[9px] text-muted-foreground">{doc.currency}</span>
                        </div>
                      </div>

                      {/* ── Delete button — always in DOM, hidden via opacity ── */}
                      {!isConfirming && !isDeleting && (
                        <button
                          id={`delete-doc-${doc.source}`}
                          onClick={() => setConfirmId(doc.source)}
                          title={`Xóa "${doc.source}"`}
                          aria-label={`Xóa tài liệu ${doc.source}`}
                          className="
                            shrink-0 ml-1
                            h-6 w-6 rounded
                            flex items-center justify-center
                            opacity-0 group-hover:opacity-100
                            text-muted-foreground
                            hover:text-red-500 hover:bg-red-500/10
                            transition-all duration-150
                            focus:outline-none focus:opacity-100
                            focus-visible:ring-1 focus-visible:ring-red-400
                          "
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>

                    {/* ── Inline 2-step confirmation ── */}
                    {isConfirming && (
                      <div className="mt-2 pt-1.5 border-t border-red-300/40 space-y-1.5">
                        <p className="text-[10px] text-red-600 dark:text-red-400 font-semibold leading-tight">
                          Xóa tất cả dữ liệu liên quan (chunks, embeddings)?  
                        </p>
                        <div className="flex gap-1.5">
                          <button
                            id={`cancel-delete-${doc.source}`}
                            onClick={() => setConfirmId(null)}
                            className="flex-1 text-[11px] py-1 rounded border border-border bg-background hover:bg-muted transition-colors font-medium"
                          >
                            Hủy
                          </button>
                          <button
                            id={`confirm-delete-${doc.source}`}
                            onClick={() => handleConfirmDelete(doc.source)}
                            className="flex-1 text-[11px] py-1 rounded bg-red-500 text-white hover:bg-red-600 transition-colors font-semibold"
                          >
                            Xóa
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Page header */}
        <div className="px-6 py-3 border-b bg-background/80 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-2">
            <Upload className="h-4 w-4 text-teal-500" />
            <h1 className="text-base font-bold">Tải lên báo cáo tài chính</h1>
            <span className="text-muted-foreground text-xs ml-1">· Xử lý PDF cho hệ thống RAG</span>
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex gap-4 p-4">

          {/* ── Upload form ── */}
          <div className="flex-1 flex flex-col gap-3 min-w-0">
            <DropZone onFileSelect={selectFile} disabled={isProcessing} currentFile={file} compact />

            <Card className="shrink-0">
              <CardHeader className="px-4 py-2.5 pb-0">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Settings2 className="h-4 w-4 text-teal-500" />
                  Cấu hình xử lý
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    id="resetDb"
                    checked={resetDatabase}
                    onChange={(e) => setResetDatabase(e.target.checked)}
                    disabled={isProcessing}
                    className="h-4 w-4 rounded border-gray-300 accent-teal-600"
                  />
                  <span className="text-sm">Xóa database trước khi xử lý</span>
                </label>
              </CardContent>
            </Card>

            <div className="flex gap-2 shrink-0">
              <Button
                onClick={() => upload(resetDatabase, 1000)}
                disabled={!file || isProcessing}
                className={`flex-1 relative overflow-hidden h-11 text-base font-semibold transition-all duration-200 ${
                  isProcessing
                    ? 'bg-gradient-to-r from-teal-600 to-cyan-600 cursor-not-allowed opacity-70'
                    : 'bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600'
                }`}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    <span>Đang xử lý... {progress}%</span>
                    <div
                      className="absolute bottom-0 left-0 h-1 bg-white/30 transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    <span>Tải lên &amp; Xử lý</span>
                  </>
                )}
              </Button>
              {isDone && (
                <Button variant="outline" onClick={reset} className="h-11 gap-1.5">
                  <RotateCcw className="h-4 w-4" />
                  Làm mới
                </Button>
              )}
            </div>

            {error && (
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-3 flex items-start gap-2 text-sm text-destructive shrink-0">
                <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {result && status === 'success' && (
              <Card className="border-emerald-500/30 bg-emerald-500/5 shrink-0">
                <CardContent className="px-4 py-3">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                    <span className="font-semibold text-emerald-700 dark:text-emerald-400">Xử lý thành công!</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                    <StatCard icon={<FileText className="h-4 w-4" />} label="Tên tài liệu"  value={result.source_name} />
                    <StatCard icon={<Layers   className="h-4 w-4" />} label="Số đoạn văn"  value={String(result.total_chunks)} />
                    <StatCard icon={<Database className="h-4 w-4" />} label="Embeddings"   value={String(result.total_embeddings)} />
                    <StatCard icon={<Clock    className="h-4 w-4" />} label="Thời gian"    value={`${result.processing_time_seconds}s`} />
                    {result.extraction_method && (
                      <StatCard icon={<BookOpen className="h-4 w-4" />} label="Phương pháp" value={result.extraction_method} />
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* ── Processing steps ── */}
          <div className="w-64 shrink-0 flex flex-col">
            <Card className="flex-1 flex flex-col overflow-hidden">
              <CardHeader className="px-4 py-2.5 pb-0 shrink-0">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layers className="h-4 w-4 text-teal-500" />
                  Tiến trình xử lý
                </CardTitle>
              </CardHeader>
              <CardContent className="px-3 pt-3 pb-3 flex-1 overflow-y-auto">
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>
                      {isProcessing ? 'Đang xử lý...' : status === 'success' ? 'Hoàn thành' : status === 'error' ? 'Lỗi' : 'Chờ bắt đầu'}
                    </span>
                    <span className="font-mono">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-1.5" />
                </div>

                <div className="space-y-1">
                  {steps.map((step, i) => (
                    <div key={step.id} className="flex items-start gap-2.5">
                      <div
                        className="flex flex-col items-center shrink-0"
                        style={{ minHeight: i < steps.length - 1 ? 44 : 24 }}
                      >
                        <div className={`h-5 w-5 rounded-full flex items-center justify-center mt-0.5 shrink-0 transition-all duration-500 ${
                          step.status === 'done'   ? 'bg-teal-500 text-white' :
                          step.status === 'active' ? 'bg-blue-500 text-white ring-4 ring-blue-500/20' :
                          step.status === 'error'  ? 'bg-destructive text-white' :
                          'bg-muted text-muted-foreground'
                        }`}>
                          {step.status === 'done'   ? <CheckCircle className="h-3 w-3" /> :
                           step.status === 'active' ? <Loader2 className="h-3 w-3 animate-spin" /> :
                           step.status === 'error'  ? <XCircle className="h-3 w-3" /> :
                           <span className="text-[9px] font-bold">{i + 1}</span>}
                        </div>
                        {i < steps.length - 1 && (
                          <div className={`w-px flex-1 mt-0.5 transition-colors duration-500 ${
                            step.status === 'done' ? 'bg-teal-400/60' : 'bg-border'
                          }`} />
                        )}
                      </div>
                      <div className="pt-0.5 pb-3 min-w-0">
                        <p className={`text-xs font-medium leading-tight ${
                          step.status === 'active' ? 'text-blue-600 dark:text-blue-400' :
                          step.status === 'done'   ? 'text-teal-700 dark:text-teal-400' :
                          step.status === 'error'  ? 'text-destructive' :
                          'text-muted-foreground'
                        }`}>
                          {step.label}
                        </p>
                        {step.status === 'active' && (
                          <p className="text-[10px] text-muted-foreground mt-0.5 leading-tight">{step.description}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg bg-background/60 border px-3 py-2">
      <span className="text-teal-500 mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] text-muted-foreground leading-none">{label}</p>
        <p className="text-sm font-semibold truncate mt-0.5">{value}</p>
      </div>
    </div>
  );
}
