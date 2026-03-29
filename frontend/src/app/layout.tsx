import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Ski Analyzer - スキーフォーム解析",
  description: "AIがあなたのスキーフォームを解析し、改善ポイントをアドバイスします",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <header className="border-b bg-white px-6 py-3">
          <div className="mx-auto flex max-w-7xl items-center gap-3">
            <span className="text-2xl">🎿</span>
            <h1 className="text-lg font-bold text-blue-900">Ski Analyzer</h1>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
