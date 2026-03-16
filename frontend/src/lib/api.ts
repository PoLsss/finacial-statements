/**
 * API Client
 */

import type {
  ChatRequest,
  ChatResponse,
  UploadResponse,
  StatusResponse,
  StreamEvent,
  DashboardResponse,
  CompaniesResponse,
  FinancialDataResponse,
  PageContentResponse,
  ExplainRequest,
  ExplainResponse,
  DeleteDocumentResponse,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:2602';

/**
 * Send a chat message and get a response
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Chat error: ${error}`);
  }

  return response.json();
}

/**
 * Send a chat message with streaming response
 */
export async function sendChatMessageStream(
  request: ChatRequest,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Chat error: ${error}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          onEvent(data as StreamEvent);
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}

/**
 * Upload and process a PDF file
 */
export async function uploadPDF(
  file: File,
  resetDatabase: boolean = false,
  chunkSize: number = 1000,
  onProgress?: (progress: number, step: string) => void
): Promise<UploadResponse> {
  // Simulate progress for upload phase
  onProgress?.(10, 'Uploading file...');
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('reset_database', String(resetDatabase));
  formData.append('chunk_size', String(chunkSize));

  onProgress?.(20, 'Parsing PDF with Landing AI...');

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  onProgress?.(90, 'Finalizing...');

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Upload error: ${error}`);
  }

  onProgress?.(100, 'Complete!');
  return response.json();
}

/**
 * Get system status
 */
export async function getStatus(): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/status`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Status error: ${error}`);
  }

  return response.json();
}

/**
 * Get dashboard summary data
 */
export async function getDashboard(): Promise<DashboardResponse> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Dashboard error: ${error}`);
  }
  return response.json();
}

/**
 * Get list of companies with financial data
 */
export async function getCompanies(): Promise<CompaniesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/statistics/companies`);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Companies error: ${error}`);
  }
  return response.json();
}

/**
 * Get industry averages for financial ratios
 */
export async function getIndustryAverages(): Promise<{ success: boolean; data?: Record<string, number>; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/statistics/industry-averages`);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Industry averages error: ${error}`);
  }
  return response.json();
}

/**
 * Get financial data for a specific company
 */
export async function getFinancialData(source: string): Promise<FinancialDataResponse> {
  const response = await fetch(`${API_BASE_URL}/api/statistics/financial-data/${encodeURIComponent(source)}`);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Financial data error: ${error}`);
  }
  return response.json();
}

/**
 * Get page content for PDF viewer
 */
export async function getPageContent(source: string, pageNumber: number): Promise<PageContentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/statistics/page-content/${encodeURIComponent(source)}/${pageNumber}`);
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Page content error: ${error}`);
  }
  return response.json();
}

/**
 * Get LLM explanation for financial ratios
 */
export async function explainRatios(request: ExplainRequest): Promise<ExplainResponse> {
  const response = await fetch(`${API_BASE_URL}/api/statistics/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Explain error: ${error}`);
  }
  return response.json();
}

/**
 * Get URL for a PDF page image (plain render)
 */
export function getPdfPageUrl(source: string, pageNumber: number, dpi = 150): string {
  return `${API_BASE_URL}/api/statistics/pdf-page/${encodeURIComponent(source)}/${pageNumber}?dpi=${dpi}`;
}

/**
 * Get URL for a PDF page image with highlighted bounding box
 */
export function getPdfPageHighlightUrl(
  source: string,
  pageNumber: number,
  box: { left: number; top: number; right: number; bottom: number },
  dpi = 150,
): string {
  const params = new URLSearchParams({
    left: String(box.left),
    top: String(box.top),
    right: String(box.right),
    bottom: String(box.bottom),
    dpi: String(dpi),
  });
  return `${API_BASE_URL}/api/statistics/pdf-page-highlight/${encodeURIComponent(source)}/${pageNumber}?${params}`;
}

/**
 * Get PDF page count info
 */
export async function getPdfInfo(source: string): Promise<{ success: boolean; page_count?: number; error?: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/statistics/pdf-info/${encodeURIComponent(source)}`
  );
  if (!response.ok) {
    throw new Error('Failed to get PDF info');
  }
  return response.json();
}

/**
 * Delete a document and all its associated data (chunks, embeddings, variables)
 */
export async function deleteDocument(sourceName: string): Promise<DeleteDocumentResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/documents/${encodeURIComponent(sourceName)}`,
    { method: 'DELETE' }
  );

  if (!response.ok && response.status !== 404) {
    const error = await response.text();
    throw new Error(`Delete error: ${error}`);
  }

  return response.json();
}
