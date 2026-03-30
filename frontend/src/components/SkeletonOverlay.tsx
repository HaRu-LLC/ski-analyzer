"use client";

import { useEffect, useRef } from "react";
import type { FrameData } from "@/types/analysis";

interface Props {
  frameData: FrameData | null;
  width: number;
  height: number;
  visible: boolean;
}

const BONE_CONNECTIONS: [string, string][] = [
  ["l_hip", "l_knee"],
  ["r_hip", "r_knee"],
  ["l_hip", "r_hip"],
  ["l_shoulder", "l_elbow"],
  ["l_elbow", "l_wrist"],
  ["r_shoulder", "r_elbow"],
  ["r_elbow", "r_wrist"],
  ["l_shoulder", "r_shoulder"],
  ["l_shoulder", "l_hip"],
  ["r_shoulder", "r_hip"],
  ["neck", "head"],
  ["l_shoulder", "neck"],
  ["r_shoulder", "neck"],
  ["spine1", "spine2"],
  ["spine2", "spine3"],
  ["spine3", "neck"],
  ["l_hip", "spine1"],
  ["r_hip", "spine1"],
];

const CONFIDENCE_COLORS: Record<string, string> = {
  high: "#22c55e",   // green-500
  medium: "#eab308", // yellow-500
  low: "#ef4444",    // red-500
};

export function SkeletonOverlay({ frameData, width, height, visible }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    if (!visible || !frameData) return;

    const positions = frameData.joint_positions_3d;
    const confidenceMap = new Map<string, string>();
    for (const angle of frameData.joint_angles) {
      confidenceMap.set(angle.joint_name, angle.confidence);
    }

    const toPixel = (pos: number[]): [number, number] | null => {
      if (!pos || pos.length < 2) return null;
      return [(pos[0] + 1) * width * 0.5, (1 - pos[1]) * height * 0.5];
    };

    // Draw bones
    ctx.lineWidth = 2;
    for (const [j1, j2] of BONE_CONNECTIONS) {
      if (!(j1 in positions) || !(j2 in positions)) continue;
      const p1 = toPixel(positions[j1]);
      const p2 = toPixel(positions[j2]);
      if (!p1 || !p2) continue;

      const conf1 = confidenceMap.get(j1) || "low";
      const conf2 = confidenceMap.get(j2) || "low";
      const boneColor =
        conf1 === "high" && conf2 === "high"
          ? CONFIDENCE_COLORS.high
          : conf1 === "low" || conf2 === "low"
            ? CONFIDENCE_COLORS.low
            : CONFIDENCE_COLORS.medium;

      ctx.strokeStyle = boneColor;
      ctx.beginPath();
      ctx.moveTo(p1[0], p1[1]);
      ctx.lineTo(p2[0], p2[1]);
      ctx.stroke();
    }

    // Draw joints
    for (const [name, pos] of Object.entries(positions)) {
      const pt = toPixel(pos);
      if (!pt) continue;

      const confidence = confidenceMap.get(name) || "low";
      ctx.fillStyle = CONFIDENCE_COLORS[confidence] || CONFIDENCE_COLORS.low;
      ctx.beginPath();
      ctx.arc(pt[0], pt[1], 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [frameData, visible, width, height]);

  if (!visible || !frameData) return null;

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      role="img"
      aria-label="スケルトンオーバーレイ"
      className="absolute inset-0 h-full w-full"
    />
  );
}
