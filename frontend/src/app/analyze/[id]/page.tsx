"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { VideoPlayer } from "@/components/VideoPlayer";
import { AnglePanel } from "@/components/AnglePanel";
import { AngleGraph } from "@/components/AngleGraph";
import { CoachingPanel } from "@/components/CoachingPanel";
import { DownloadBar } from "@/components/DownloadBar";
import { ProgressIndicator } from "@/components/ProgressIndicator";
import { useAnalysis } from "@/hooks/useAnalysis";

export default function AnalyzePage() {
  const params = useParams();
  const analysisId = params.id as string;

  const [currentFrame, setCurrentFrame] = useState(0);
  const { status, progress, eta, result, error } = useAnalysis({ analysisId });

  // 解析中画面 (S-002)
  if (!result) {
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
            videoWidth={result.video_info.width}
            videoHeight={result.video_info.height}
            hasOverlayVideo={result.artifacts.video}
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
      <DownloadBar analysisId={analysisId} artifacts={result.artifacts} />
    </div>
  );
}
