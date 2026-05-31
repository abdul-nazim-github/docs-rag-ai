import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Docs RAG AI — Intelligent Document Q&A",
  description:
    "Upload documents and ask questions powered by AI. " +
    "Retrieval-Augmented Generation with OpenAI and FAISS vector search.",
  keywords: ["RAG", "AI", "document", "Q&A", "OpenAI", "FAISS", "LangChain"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
