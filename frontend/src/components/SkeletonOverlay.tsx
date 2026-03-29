"use client";

/**
 * Three.js による3Dスケルトン重畳表示コンポーネント.
 *
 * TODO: Three.js + @react-three/fiber で実装
 * - SMPL骨格構造に基づく関節ポイント描画
 * - 関節間のボーン（骨）をライン描画
 * - 関節ごとの色分け（精度レベルに応じて）
 * - 動画フレームとの同期
 */

import type { FrameData } from "@/types/analysis";

interface Props {
  frameData: FrameData | null;
  width: number;
  height: number;
  visible: boolean;
}

// SMPL骨格のボーン接続定義
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

export function SkeletonOverlay({ frameData, width, height, visible }: Props) {
  if (!visible || !frameData) return null;

  // TODO: Three.js Canvas実装に置き換え
  // 現状はVideoPlayer内のCanvas 2D描画で代替
  return null;
}
