"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FrameData } from "@/types/analysis";

interface Props {
  analysisId: string;
  totalFrames: number;
  fps: number;
  currentFrame: number;
  onFrameChange: (frame: number) => void;
  frameData: FrameData | null;
}

type PlaybackSpeed = 0.25 | 0.5 | 1 | 2;

export function VideoPlayer({
  analysisId,
  totalFrames,
  fps,
  currentFrame,
  onFrameChange,
  frameData,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<PlaybackSpeed>(1);
  const [showSkeleton, setShowSkeleton] = useState(true);

  // キーボードショートカット
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      switch (e.code) {
        case "Space":
          e.preventDefault();
          setPlaying((p) => !p);
          break;
        case "ArrowLeft":
          e.preventDefault();
          onFrameChange(Math.max(0, currentFrame - 1));
          break;
        case "ArrowRight":
          e.preventDefault();
          onFrameChange(Math.min(totalFrames - 1, currentFrame + 1));
          break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentFrame, totalFrames, onFrameChange]);

  // 再生制御
  useEffect(() => {
    if (!playing) return;
    const interval = setInterval(() => {
      onFrameChange((prev: number) => {
        const next = prev + 1;
        if (next >= totalFrames) {
          setPlaying(false);
          return prev;
        }
        return next;
      });
    }, 1000 / fps / speed);
    return () => clearInterval(interval);
  }, [playing, fps, speed, totalFrames, onFrameChange]);

  // スケルトン描画
  useEffect(() => {
    if (!showSkeleton || !frameData || !canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);

    // TODO: Three.js による3Dスケルトン描画を実装
    // 暫定: 2Dキーポイント描画
    const positions = frameData.joint_positions_3d;
    const w = canvasRef.current.width;
    const h = canvasRef.current.height;

    ctx.strokeStyle = "#00ff88";
    ctx.lineWidth = 2;
    ctx.fillStyle = "#00ff88";

    Object.values(positions).forEach(([x, y]) => {
      const px = (x + 1) * w * 0.5;
      const py = (1 - y) * h * 0.5;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [frameData, showSkeleton]);

  const speeds: PlaybackSpeed[] = [0.25, 0.5, 1, 2];

  return (
    <div className="rounded-xl border bg-gray-900 p-3 shadow-sm">
      {/* 動画 + スケルトンオーバーレイ */}
      <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
        <video
          ref={videoRef}
          className="absolute inset-0 h-full w-full object-contain"
          src={`${process.env.NEXT_PUBLIC_API_URL}/api/download/${analysisId}/video`}
        />
        <canvas
          ref={canvasRef}
          className="absolute inset-0 h-full w-full"
          width={1920}
          height={1080}
        />
      </div>

      {/* コントロールバー */}
      <div className="mt-3 flex flex-col gap-2">
        {/* シークバー */}
        <input
          type="range"
          min={0}
          max={totalFrames - 1}
          value={currentFrame}
          onChange={(e) => onFrameChange(Number(e.target.value))}
          className="w-full cursor-pointer accent-blue-500"
        />

        <div className="flex items-center justify-between text-sm text-gray-300">
          {/* 左: 再生コントロール */}
          <div className="flex items-center gap-2">
            {/* コマ戻し */}
            <button
              onClick={() => onFrameChange(Math.max(0, currentFrame - 1))}
              className="rounded px-2 py-1 hover:bg-gray-700"
              title="前のフレーム (←)"
            >
              ⏮
            </button>

            {/* 再生/停止 */}
            <button
              onClick={() => setPlaying(!playing)}
              className="rounded px-3 py-1 hover:bg-gray-700"
              title="再生/停止 (Space)"
            >
              {playing ? "⏸" : "▶"}
            </button>

            {/* コマ送り */}
            <button
              onClick={() => onFrameChange(Math.min(totalFrames - 1, currentFrame + 1))}
              className="rounded px-2 py-1 hover:bg-gray-700"
              title="次のフレーム (→)"
            >
              ⏭
            </button>

            {/* 速度 */}
            <div className="ml-2 flex gap-1">
              {speeds.map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`rounded px-2 py-0.5 text-xs ${
                    speed === s ? "bg-blue-600 text-white" : "hover:bg-gray-700"
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          {/* 中央: フレーム番号 */}
          <span className="font-mono">
            {currentFrame + 1} / {totalFrames}
          </span>

          {/* 右: スケルトン表示切替 */}
          <button
            onClick={() => setShowSkeleton(!showSkeleton)}
            className={`rounded px-3 py-1 text-xs ${
              showSkeleton ? "bg-green-600 text-white" : "bg-gray-700"
            }`}
          >
            🦴 {showSkeleton ? "ON" : "OFF"}
          </button>
        </div>
      </div>
    </div>
  );
}
