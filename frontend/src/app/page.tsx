"use client";

import { useCallback, useEffect, useState } from "react";
import Header from "@/components/Header";
import DocumentPanel from "@/components/DocumentPanel";
import ChatPanel from "@/components/ChatPanel";
import { getDocuments } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

/**
 * Main page — orchestrates the document panel and chat panel.
 * Manages document list state and refreshes on upload/delete.
 */
export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);

  // ── Fetch documents ───────────────────────────────────────────────────────

  const fetchDocuments = useCallback(async () => {
    try {
      const response = await getDocuments();
      setDocuments(response.documents);
    } catch {
      // Backend might not be running yet — fail silently
      console.warn("Could not fetch documents. Is the backend running?");
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="app-layout">
      <Header />
      <div className="app-body">
        <DocumentPanel
          documents={documents}
          onDocumentsChange={fetchDocuments}
        />
        <ChatPanel hasDocuments={documents.length > 0} />
      </div>
    </div>
  );
}
