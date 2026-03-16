/**
 * API Types
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  question: string;
  history?: ChatMessage[];
  use_agent?: boolean | null;
}

export interface ChunkMetadata {
  source: string;
  page_index: number;
  chunk_id: number;
  tokens: number;
  has_table: boolean;
}

export interface Chunk {
  page_content: string;
  metadata: ChunkMetadata | Record<string, unknown>;
}

export interface RoutingMetadata {
  complexity_level: string;
  complexity_score: number;
  routing_decision: string;
  reasoning?: string;
  agent_mode?: boolean;
  analysis_type?: string;
  agent_steps?: string[];
  insights_count?: number;
  sources?: string[];
}

export interface ChatData {
  answer: string;
  chunks: Chunk[];
  routing_metadata: RoutingMetadata;
}

export interface ChatResponse {
  success: boolean;
  data?: ChatData;
  error?: string;
}

// Streaming types
export interface ThinkingStep {
  type: 'thinking';
  step: string;
  message: string;
}

export interface RoutingEvent {
  type: 'routing';
  decision: string;
  score: number;
  message: string;
}

export interface ChunksEvent {
  type: 'chunks';
  chunks: Chunk[];
}

export interface TokenEvent {
  type: 'token';
  content: string;
  full_content: string;
}

export interface MetadataEvent {
  type: 'metadata';
  routing_metadata: RoutingMetadata;
}

export interface DoneEvent {
  type: 'done';
  success: boolean;
}

export interface ErrorEvent {
  type: 'error';
  error: string;
}

export type StreamEvent = ThinkingStep | RoutingEvent | ChunksEvent | TokenEvent | MetadataEvent | DoneEvent | ErrorEvent;

export interface UploadData {
  source_name: string;
  total_chunks: number;
  total_embeddings: number;
  financial_extraction: boolean;
  extraction_method?: string;
  ratios_computed: boolean;
  processing_time_seconds: number;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  data?: UploadData;
  error?: string;
  error_code?: string;
}

export interface ServicesStatus {
  openai: boolean;
  landing_ai: boolean;
  chromadb?: boolean;
  mongodb?: boolean;
}

export interface StatusData {
  database_initialized: boolean;
  collection_name?: string;
  total_documents?: number;
  total_chunks?: number;
  total_embeddings?: number;
  total_variables?: number;
  embedding_model: string;
  llm_model: string;
  services: ServicesStatus;
}

export interface StatusResponse {
  success: boolean;
  data?: StatusData;
  error?: string;
}

// Dashboard types
export interface DashboardData {
  total_documents: number;
  total_chunks: number;
  total_embeddings: number;
  total_cost: number;
  total_tokens: number;
}

export interface DashboardResponse {
  success: boolean;
  data?: DashboardData;
  error?: string;
}

// Statistics types
export interface CompanyInfo {
  source: string;
  company: string;
  period: string;
  currency: string;
}

export interface CompaniesResponse {
  success: boolean;
  data?: CompanyInfo[];
  error?: string;
}

export interface FieldMetadata {
  value: number | string | null;
  page?: number;
  location?: {
    left: number;
    top: number;
    right: number;
    bottom: number;
  };
  chunk_type?: string;
  chunk_id?: string;
  error?: string;
}

export interface RatioData {
  formula: string;
  result: number | null;
  error?: string;
  fields: Record<string, FieldMetadata>;
}

export interface FinancialData {
  source: string;
  company: string;
  period: string;
  currency: string;
  extraction_method: string;
  extracted_fields: Record<string, FieldMetadata>;
  calculated_ratios: Record<string, RatioData>;
  z_score?: ZScoreData;
}

export interface ZScoreVariable {
  formula: string;
  result: number | null;
  fields: Record<string, FieldMetadata>;
}

export interface ZScoreData {
  variables: Record<string, ZScoreVariable>;
  z_value: number | null;
  z_formula: string;
  classification: 'safe' | 'grey' | 'danger' | 'unknown';
}

export interface FinancialDataResponse {
  success: boolean;
  data?: FinancialData;
  error?: string;
}

export interface PageContentResponse {
  success: boolean;
  page_text?: string;
  page_number?: number;
  error?: string;
}

export interface ExplainRequest {
  group_name: string;
  group_label: string;
  ratios: Record<string, RatioData>;
  thresholds: Record<string, { value: number; label: string }>;
}

export interface ExplainResponse {
  success: boolean;
  explanation?: string;
  recommendations?: string;
  error?: string;
}

// Document deletion
export interface DeleteDocumentResponse {
  success: boolean;
  message: string;
  deleted_chunks?: number;
  deleted_embeddings?: number;
  deleted_variables?: number;
  error?: string;
}
