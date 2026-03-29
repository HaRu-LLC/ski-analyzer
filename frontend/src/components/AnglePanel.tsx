"use client";

import type { FrameData } from "@/types/analysis";

interface Props {
  frameData: FrameData | null;
}

const CONFIDENCE_COLORS = {
  high: "text-green-600",
  medium: "text-yellow-600",
  low: "text-gray-400",
};

const CONFIDENCE_LABELS = {
  high: "",
  medium: "",
  low: "参考値",
};

export function AnglePanel({ frameData }: Props) {
  if (!frameData) {
    return (
      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <p className="text-sm text-gray-400">フレームを選択してください</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-gray-700">
        関節角度（フレーム {frameData.frame_index + 1}）
      </h3>
      <div className="space-y-1.5">
        {frameData.joint_angles.map((angle) => (
          <div
            key={angle.joint_name}
            className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-gray-50"
          >
            <span className="font-medium text-gray-700">{angle.joint_name_ja}</span>
            <div className="flex items-center gap-2">
              {angle.flexion !== null && (
                <span className={CONFIDENCE_COLORS[angle.confidence]}>
                  {angle.flexion > 0 ? "+" : ""}
                  {angle.flexion}°
                </span>
              )}
              {CONFIDENCE_LABELS[angle.confidence] && (
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-400">
                  {CONFIDENCE_LABELS[angle.confidence]}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
