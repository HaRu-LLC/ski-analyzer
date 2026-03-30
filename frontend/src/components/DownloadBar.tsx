"use client";

import { getDownloadUrl } from "@/utils/api";
import type { AnalysisArtifacts } from "@/types/analysis";

interface Props {
  analysisId: string;
  artifacts: AnalysisArtifacts;
}

export function DownloadBar({ analysisId, artifacts }: Props) {
  const downloads = [
    { type: "video" as const, label: "解析動画 (MP4)", icon: "🎬", available: artifacts.video },
    { type: "report" as const, label: "レポート (PDF)", icon: "📄", available: artifacts.report },
    { type: "csv" as const, label: "数値データ (CSV)", icon: "📊", available: artifacts.csv },
  ];

  return (
    <div className="flex items-center justify-center gap-3 rounded-xl border bg-white px-6 py-4 shadow-sm">
      <span className="text-sm font-medium text-gray-600">ダウンロード:</span>
      {downloads.map(({ type, label, icon, available }) =>
        available ? (
          <a
            key={type}
            href={getDownloadUrl(analysisId, type)}
            download
            className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
          >
            {icon} {label}
          </a>
        ) : (
          <span
            key={type}
            aria-disabled="true"
            className="flex cursor-not-allowed items-center gap-1.5 rounded-lg border border-gray-200 bg-gray-100 px-4 py-2 text-sm font-medium text-gray-400"
          >
            {icon} {label}
          </span>
        )
      )}
    </div>
  );
}
