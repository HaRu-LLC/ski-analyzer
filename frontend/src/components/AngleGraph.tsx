"use client";

import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer,
} from "recharts";
import type { FrameData } from "@/types/analysis";

interface Props {
  frames: FrameData[];
  currentFrame: number;
  onFrameSelect: (frame: number) => void;
}

const JOINT_OPTIONS = [
  { key: "l_knee", label: "左膝" },
  { key: "r_knee", label: "右膝" },
  { key: "l_hip", label: "左股関節" },
  { key: "r_hip", label: "右股関節" },
  { key: "l_shoulder", label: "左肩" },
  { key: "r_shoulder", label: "右肩" },
  { key: "spine2", label: "脊椎（胸郭）" },
];

const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b"];

export function AngleGraph({ frames, currentFrame, onFrameSelect }: Props) {
  const [selectedJoints, setSelectedJoints] = useState<string[]>(["l_knee", "r_knee"]);

  const toggleJoint = (key: string) => {
    setSelectedJoints((prev) =>
      prev.includes(key)
        ? prev.filter((k) => k !== key)
        : prev.length < 4
          ? [...prev, key]
          : prev
    );
  };

  // グラフデータ構築
  const data = frames.map((frame) => {
    const point: Record<string, number> = { frame: frame.frame_index };
    for (const joint of selectedJoints) {
      const angle = frame.joint_angles.find((a) => a.joint_name === joint);
      if (angle?.flexion !== null && angle?.flexion !== undefined) {
        point[joint] = angle.flexion;
      }
    }
    return point;
  });

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">関節角度の推移</h3>

      {/* 関節選択 */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {JOINT_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => toggleJoint(opt.key)}
            className={`rounded-full px-2.5 py-0.5 text-xs transition-colors ${
              selectedJoints.includes(opt.key)
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-500 hover:bg-gray-200"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* グラフ */}
      <ResponsiveContainer width="100%" height={200}>
        <LineChart
          data={data}
          onClick={(e) => {
            if (e?.activeLabel !== undefined) {
              onFrameSelect(Number(e.activeLabel));
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="frame" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} unit="°" />
          <Tooltip
            formatter={(value: number) => `${value.toFixed(1)}°`}
            labelFormatter={(label) => `フレーム ${Number(label) + 1}`}
          />
          <ReferenceLine
            x={currentFrame}
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="4 4"
          />
          {selectedJoints.map((joint, i) => (
            <Line
              key={joint}
              type="monotone"
              dataKey={joint}
              stroke={COLORS[i % COLORS.length]}
              dot={false}
              strokeWidth={1.5}
              name={JOINT_OPTIONS.find((o) => o.key === joint)?.label}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
