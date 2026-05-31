"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { queryRAGStream } from "@/lib/api";
import type { ChatMessage, SourceInfo } from "@/lib/types";

interface ChatPanelProps {
  hasDocuments: boolean;
}

/**
 * Conversational chat interface — user bubbles on the right,
 * assistant bubbles on the left with markdown rendering.
 */
export default function ChatPanel({ hasDocuments }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  // ── Send message ────────────────────────────────────────────────────────

  const sendMessage = useCallback(async () => {
    const question = input.trim();
    if (!question || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    const assistantId = crypto.randomUUID();
    const initialAssistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      sources: [],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await queryRAGStream(question);
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Failed to get reader from response stream.");
      }

      const decoder = new TextDecoder("utf-8");
      let assistantContent = "";
      let assistantSources: SourceInfo[] = [];
      let buffer = "";

      setIsLoading(false);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          const jsonStr = trimmed.slice(6);
          try {
            const chunk = JSON.parse(jsonStr);
            if (chunk.type === "sources") {
              assistantSources = chunk.sources;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, sources: assistantSources }
                    : msg
                )
              );
            } else if (chunk.type === "content") {
              assistantContent += chunk.content;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, content: assistantContent }
                    : msg
                )
              );
            } else if (chunk.type === "error") {
              throw new Error(chunk.content);
            }
          } catch (err) {
            console.error("Error parsing stream chunk:", err);
          }
        }
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? `Sorry, an error occurred: ${err.message}`
          : "Sorry, something went wrong. Please try again.";

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? { ...msg, content: errorMessage }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }, [input, isLoading]);

  // ── Key handler ───────────────────────────────────────────────────────

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage]
  );

  // ── Format timestamp ──────────────────────────────────────────────────

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <main className="chat-panel">
      {/* Message list */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h2 className="chat-empty-title">Ask your documents anything</h2>
            <p className="chat-empty-description">
              {hasDocuments
                ? "Your documents are indexed and ready. Type a question below to get started."
                : "Upload documents using the panel on the left, then ask questions about them here."}
            </p>
            {hasDocuments && (
              <div className="chat-suggestions">
                <button
                  className="suggestion-chip"
                  onClick={() => {
                    setInput("What is the main topic of the uploaded documents?");
                    inputRef.current?.focus();
                  }}
                >
                  💡 What is the main topic?
                </button>
                <button
                  className="suggestion-chip"
                  onClick={() => {
                    setInput("Summarize the key points from the documents.");
                    inputRef.current?.focus();
                  }}
                >
                  📝 Summarize key points
                </button>
                <button
                  className="suggestion-chip"
                  onClick={() => {
                    setInput("What are the most important findings?");
                    inputRef.current?.focus();
                  }}
                >
                  🔍 Important findings
                </button>
              </div>
            )}
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`msg-row ${msg.role === "user" ? "msg-row--user" : "msg-row--assistant"}`}
            >
              {/* Avatar — shown on the outer edge of each bubble */}
              {msg.role === "assistant" && (
                <div className="msg-avatar msg-avatar--assistant">
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
                    <path d="M12 2L2 7l10 5 10-5-10-5z" />
                    <path d="M2 17l10 5 10-5" />
                    <path d="M2 12l10 5 10-5" />
                  </svg>
                </div>
              )}

              <div className={`msg-bubble ${msg.role === "user" ? "msg-bubble--user" : "msg-bubble--assistant"}`}>
                {/* Role label + time */}
                <div className="msg-meta">
                  <span className="msg-role">
                    {msg.role === "user" ? "You" : "AI Assistant"}
                  </span>
                  <span className="msg-time">{formatTime(msg.timestamp)}</span>
                </div>

                {/* Message body */}
                <div className="msg-body">
                  {msg.role === "assistant" ? (
                    /* Render markdown for assistant replies */
                    <ReactMarkdown>{msg.content || "…"}</ReactMarkdown>
                  ) : (
                    /* Plain text for user messages */
                    msg.content.split("\n").map((line, i) => (
                      <p key={i}>{line || "\u00A0"}</p>
                    ))
                  )}
                </div>

                {/* Source citations — assistant only */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="msg-sources">
                    <span className="msg-sources__label">Sources</span>
                    {msg.sources.map((source, i) => (
                      <div key={i} className="msg-source-chip">
                        <span className="msg-source-chip__name">
                          📄 {source.filename}
                        </span>
                        <span className="msg-source-chip__snippet">
                          {source.snippet}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="msg-avatar msg-avatar--user">
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
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="msg-row msg-row--assistant">
            <div className="msg-avatar msg-avatar--assistant">
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
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div className="msg-bubble msg-bubble--assistant">
              <div className="typing-indicator">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              hasDocuments
                ? "Ask a question about your documents…"
                : "Upload documents first to start asking questions…"
            }
            disabled={isLoading}
            rows={1}
            aria-label="Chat input"
            id="chat-input"
          />
          <button
            className={`chat-send ${input.trim() && !isLoading ? "active" : ""}`}
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
            id="send-button"
          >
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
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="chat-hint">
          Press <kbd>Enter</kbd> to send · <kbd>Shift + Enter</kbd> for new line
        </p>
      </div>
    </main>
  );
}
