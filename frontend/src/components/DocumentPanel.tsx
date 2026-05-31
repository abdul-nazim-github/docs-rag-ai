"use client";

import { useCallback, useRef, useState } from "react";
import { uploadDocument, deleteDocument } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

interface DocumentPanelProps {
  documents: DocumentInfo[];
  onDocumentsChange: () => void;
}

/**
 * Sidebar panel for uploading documents and managing the document list.
 * Supports drag-and-drop plus click-to-browse.
 */
export default function DocumentPanel({
  documents,
  onDocumentsChange,
}: DocumentPanelProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DocumentInfo | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Upload handler ────────────────────────────────────────────────────────

  const handleUpload = useCallback(
    async (files: FileList | File[]) => {
      setError(null);
      setIsUploading(true);

      const fileArray = Array.from(files);
      for (let i = 0; i < fileArray.length; i++) {
        const file = fileArray[i];
        setUploadProgress(
          `Uploading ${file.name} (${i + 1}/${fileArray.length})…`
        );

        try {
          await uploadDocument(file);
        } catch (err) {
          setError(
            err instanceof Error ? err.message : `Failed to upload ${file.name}`
          );
          setIsUploading(false);
          setUploadProgress("");
          return;
        }
      }

      setIsUploading(false);
      setUploadProgress("");
      onDocumentsChange();
    },
    [onDocumentsChange]
  );

  // ── Delete handler ────────────────────────────────────────────────────────

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteDocument(id);
        onDocumentsChange();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete document"
        );
      }
    },
    [onDocumentsChange]
  );

  // ── Drag & drop handlers ──────────────────────────────────────────────────

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        handleUpload(e.dataTransfer.files);
      }
    },
    [handleUpload]
  );

  // ── Helpers ───────────────────────────────────────────────────────────────

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (filename: string): string => {
    const ext = filename.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "pdf":
        return "📄";
      case "docx":
        return "📝";
      case "md":
        return "📋";
      case "txt":
        return "📃";
      default:
        return "📎";
    }
  };

  return (
    <aside className="document-panel">
      <div className="panel-header">
        <h2 className="panel-title">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Documents
        </h2>
        <span className="panel-count">{documents.length}</span>
      </div>

      {/* Upload dropzone */}
      <div
        className={`dropzone ${isDragOver ? "drag-over" : ""} ${isUploading ? "uploading" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload documents"
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.docx"
          className="dropzone-input"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleUpload(e.target.files);
              e.target.value = "";
            }
          }}
        />

        {isUploading ? (
          <div className="dropzone-content">
            <div className="upload-spinner" />
            <p className="dropzone-text">{uploadProgress}</p>
          </div>
        ) : (
          <div className="dropzone-content">
            <svg
              className="dropzone-icon"
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="dropzone-text">
              Drop files here or <span className="dropzone-link">browse</span>
            </p>
            <p className="dropzone-hint">PDF, TXT, MD, DOCX</p>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="panel-error">
          <span>⚠️</span>
          <span>{error}</span>
          <button
            className="error-dismiss"
            onClick={() => setError(null)}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Document list */}
      <div className="document-list">
        {documents.length === 0 ? (
          <div className="document-empty">
            <p>No documents uploaded yet.</p>
            <p className="document-empty-hint">
              Upload documents to start asking questions.
            </p>
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc.id} className="document-item">
              <div className="document-info">
                <span className="document-icon">
                  {getFileIcon(doc.filename)}
                </span>
                <div className="document-meta">
                  <span className="document-name" title={doc.filename}>
                    {doc.filename}
                  </span>
                  <span className="document-size">
                    {formatSize(doc.size)}
                  </span>
                </div>
              </div>
              <button
                className="document-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteTarget(doc);
                }}
                aria-label={`Delete ${doc.filename}`}
                title="Delete document"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </button>
            </div>
          ))
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div className="modal-overlay" onClick={() => setDeleteTarget(null)}>
          <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Delete {deleteTarget.filename}?</h3>
            <p className="modal-body">This action cannot be undone.</p>
            <div className="modal-actions">
              <button
                className="btn btn--secondary"
                onClick={() => setDeleteTarget(null)}
              >
                Cancel
              </button>
              <button
                className="btn btn--danger"
                onClick={async () => {
                  const targetId = deleteTarget.id;
                  setDeleteTarget(null);
                  await handleDelete(targetId);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
