"use client";

import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

/**
 * Application header with branding and live backend health indicator.
 */
export default function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await healthCheck();
        setHealth(data);
        setIsOnline(true);
      } catch {
        setIsOnline(false);
        setHealth(null);
      }
    };

    check();
    // Poll every 30 seconds
    const interval = setInterval(check, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="header">
      <div className="header-left">
        <div className="header-logo">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="url(#logo-grad)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <defs>
              <linearGradient id="logo-grad" x1="2" y1="2" x2="22" y2="22">
                <stop stopColor="#818cf8" />
                <stop offset="1" stopColor="#c084fc" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div>
          <h1 className="header-title">Docs RAG AI</h1>
          <p className="header-subtitle">
            Intelligent Document Q&A
          </p>
        </div>
      </div>

      <div className="header-right">
        {health && (
          <span className="header-model">{health.model}</span>
        )}
        <div className={`health-indicator ${isOnline ? "online" : "offline"}`}>
          <span className="health-dot" />
          <span className="health-label">
            {isOnline ? "Connected" : "Offline"}
          </span>
        </div>
      </div>
    </header>
  );
}
