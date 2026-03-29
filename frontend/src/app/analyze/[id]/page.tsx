"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { VideoPlayer } from "@/components/VideoPlayer";
import { AnglePanel } from "@/components/AnglePanel";
import { AngleGraph } from "@/components/AngleGraph";
import { CoachingPanel } from "@/components/CoachingPanel";
import { DownloadBar } from "@/components/DownloadBar";
import { ProgressIndicator } from "@/components/ProgressIndicator";
import { getAnalysisStatus, getAnalysisResult } from "@/utils/api";
import type { AnalysisResult, AnalysisStatus } from "@/types/analysis";

export default function AnalyzePage() {
  const params = useParams();
  const analysisId = params.id as string;

  const [status, setStatus] = useState<AnalysisStatus>("validating");
  const [progress, setProgress] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // 解析状況ポーリング
  useEffect(() => {
    if (status === "completed" || status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const res = await getAnalysisStatus(analysisId);
        setStatus(res.status);
        setProgress(res.progress);
        setEta(res.estimated_remaining_seconds);

        if (res.status === "completed") {
          const analysisResult = await getAnalysisResult(analysisId);
          setResult(analysisResult);
        } else if (res.status === "failed") {
          setError(res.error_message || "解析に失敗しました");
        }
      } catch {
        // ポーリング失敗は無視（次回リトライ）
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [analysisId, status]);

  // 解析中画面 (S-002)
  if (status !== "completed") {
    return (
      <div className="flex flex-col items-center gap-6 py-20">
        <ProgressIndicator status={status} progress={progress} eta={eta} />
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
      </div>
    );
  }

  if (!result) return null;

  const currentFrameData = result.frames[currentFrame] || null;

  // 解析結果画面 (S-003)
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* 左: 動画プレイヤー + スケルトン重畳 */}
        <div className="lg:col-span-2">
          <VideoPlayer
            analysisId={analysisId}
            totalFrames={result.total_frames}
            fps={result.video_info.fps}
            currentFrame={currentFrame}
            onFrameChange={setCurrentFrame}
            frameData={currentFrameData}
          />
        </div>

        {/* 右: パネル群 */}
        <div className="flex flex-col gap-4">
          {/* 関節角度パネル */}
          <AnglePanel frameData={currentFrameData} />

          {/* 時系列グラフ */}
          <AngleGraph
            frames={result.frames}
            currentFrame={currentFrame}
            onFrameSelect={setCurrentFrame}
          />
        </div>
      </div>

      {/* AIコーチング */}
      <CoachingPanel
        coaching={result.coaching}
        idealComparison={result.ideal_comparison}
      />

      {/* ダウンロードバー */}
      <DownloadBar analysisId={analysisId} />
    </div>
  );
}
