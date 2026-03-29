"use client";

import { getDownloadUrl } from "@/utils/api";

interface Props {
  analysisId: string;
}

export function DownloadBar({ analysisId }: Props) {
  const downloads = [
    { type: "video" as const, label: "解析動画 (MP4)", icon: "🎬" },
    { type: "report" as const, label: "レポート (PDF)", icon: "📄" },
    { type: "csv" as const, label: "数値データ (CSV)", icon: "📊" },
  ];

  return (
    <div className="flex items-center justify-center gap-3 rounded-xl border bg-white px-6 py-4 shadow-sm">
      <span className="text-sm font-medium text-gray-600">ダウンロード:</span>
      {downloads.map(({ type, label, icon }) => (
        <a
          key={type}
          href={getDownloadUrl(analysisId, type)}
          download
          className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
        >
          {icon} {label}
        </a>
      ))}
    </div>
  );
}
