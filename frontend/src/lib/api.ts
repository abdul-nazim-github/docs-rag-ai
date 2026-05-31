/**
 * API client — all backend communication goes through this module.
 *
 * The backend URL is read from NEXT_PUBLIC_API_URL (set in .env.local).
 * Nothing is hardcoded.
 */

import type {
  DocumentInfo,
  HealthResponse,
  QueryResponse,
  UploadResponse,
} from "./types";

// ── Base URL from environment ─────────────────────────────────────────────────
const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  console.warn(
    "⚠️  NEXT_PUBLIC_API_URL is not set. API calls will fail. " +
      "Create a .env.local file with NEXT_PUBLIC_API_URL=http://localhost:8000"
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Wrapper around fetch that handles JSON parsing and error responses.
 */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const message =
      errorBody?.detail || `API error: ${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

// ── Upload ────────────────────────────────────────────────────────────────────

/**
 * Upload a document file to the backend for processing and indexing.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<UploadResponse>("/api/upload", {
    method: "POST",
    body: formData,
    // Note: Do NOT set Content-Type header — browser sets it with boundary
  });
}

// ── Query ─────────────────────────────────────────────────────────────────────

/**
 * Send a question to the RAG chain and receive a real-time stream of answers.
 */
export async function queryRAGStream(question: string): Promise<Response> {
  const url = `${API_URL}/api/query`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const message =
      errorBody?.detail || `API error: ${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return response;
}

// ── Documents ─────────────────────────────────────────────────────────────────

/**
 * Fetch the list of all uploaded documents.
 */
export async function getDocuments(): Promise<DocumentInfo[]> {
  return apiFetch<DocumentInfo[]>("/api/documents");
}

/**
 * Delete a specific uploaded document by ID.
 */
export async function deleteDocument(
  id: string
): Promise<{ success: boolean; message: string }> {
  return apiFetch<{ success: boolean; message: string }>(
    `/api/documents/${encodeURIComponent(id)}`,
    { method: "DELETE" }
  );
}

// ── Health ────────────────────────────────────────────────────────────────────

/**
 * Check backend health status and index statistics.
 */
export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}
