import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Memory-Augmented Chatbot",
  description: "Hybrid RAG + Knowledge Graph + Memory via LangGraph and OpenRouter",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
