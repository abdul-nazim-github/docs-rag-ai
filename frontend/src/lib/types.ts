/**
 * Shared TypeScript interfaces — mirrors the backend Pydantic schemas.
 *
 * Keep these in sync with `backend/app/api/schemas.py`.
 */

// ── Query ─────────────────────────────────────────────────────────────────────

export interface QueryRequest {
  question: string;
}

export interface SourceInfo {
  filename: string;
  snippet: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceInfo[];
}

// ── Upload ────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  filename: string;
  chunks: number;
  message: string;
}

// ── Documents ─────────────────────────────────────────────────────────────────

export interface DocumentInfo {
  filename: string;
  size: number;
  uploaded_at: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total: number;
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  indexed_documents: number;
  model: string;
}

// ── Chat UI ───────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceInfo[];
  timestamp: Date;
}
