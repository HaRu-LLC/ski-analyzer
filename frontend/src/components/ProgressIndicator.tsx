"use client";

import type { AnalysisStatus } from "@/types/analysis";

interface Props {
  status: AnalysisStatus;
  progress: number;
  eta: number | null;
}

const STATUS_LABELS: Record<AnalysisStatus, string> = {
  uploading: "アップロード中...",
  validating: "動画を検証中...",
  extracting_frames: "フレームを抽出中...",
  estimating_pose: "3Dポーズを推定中...",
  calculating_angles: "関節角度を算出中...",
  generating_coaching: "AIコーチングを生成中...",
  rendering_overlay: "スケルトン動画を生成中...",
  completed: "完了",
  failed: "エラーが発生しました",
};

export function ProgressIndicator({ status, progress, eta }: Props) {
  const isError = status === "failed";

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-4">
      {/* アニメーション */}
      {!isError && (
        <div className="text-6xl animate-bounce">🎿</div>
      )}

      {/* ステータスラベル */}
      <p className={`text-lg font-medium ${isError ? "text-red-600" : "text-gray-700"}`}>
        {STATUS_LABELS[status]}
      </p>

      {/* プログレスバー */}
      {!isError && (
        <div className="w-full">
          <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-xs text-gray-500">
            <span>{progress.toFixed(0)}%</span>
            {eta !== null && <span>残り約 {eta} 秒</span>}
          </div>
        </div>
      )}
    </div>
  );
}
