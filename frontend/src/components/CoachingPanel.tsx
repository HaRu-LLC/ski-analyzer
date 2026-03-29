"use client";

import type { CoachingAdvice, IdealComparison } from "@/types/analysis";

interface Props {
  coaching: CoachingAdvice;
  idealComparison: IdealComparison[];
}

const PRIORITY_STYLES = {
  high: "border-red-200 bg-red-50",
  medium: "border-yellow-200 bg-yellow-50",
  low: "border-gray-200 bg-gray-50",
};

const RATING_STYLES = {
  good: "bg-green-100 text-green-700",
  needs_improvement: "bg-yellow-100 text-yellow-700",
  poor: "bg-red-100 text-red-700",
};

const RATING_LABELS = {
  good: "良好",
  needs_improvement: "改善の余地",
  poor: "要改善",
};

export function CoachingPanel({ coaching, idealComparison }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* AIコーチング */}
      <div className="rounded-xl border bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">🤖 AIコーチング</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">総合スコア</span>
            <span className="rounded-full bg-blue-600 px-3 py-1 text-lg font-bold text-white">
              {coaching.overall_score}
            </span>
          </div>
        </div>

        <p className="mb-4 text-sm text-gray-600">{coaching.summary}</p>

        <div className="space-y-3">
          {coaching.details.map((detail, i) => (
            <div
              key={i}
              className={`rounded-lg border p-3 ${PRIORITY_STYLES[detail.priority]}`}
            >
              <div className="mb-1 flex items-center gap-2">
                <span className="font-medium text-gray-800">{detail.joint}</span>
                <span className="rounded bg-white px-1.5 py-0.5 text-xs text-gray-500">
                  {detail.priority === "high" ? "優先" : detail.priority === "medium" ? "中" : "低"}
                </span>
              </div>
              <p className="text-sm text-gray-700">{detail.advice}</p>
              {detail.exercise && (
                <p className="mt-1 text-xs text-gray-500">
                  💡 練習方法: {detail.exercise}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 理想フォーム比較 */}
      <div className="rounded-xl border bg-white p-5 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">📊 理想フォームとの比較</h3>
        <div className="space-y-2">
          {idealComparison.map((item) => (
            <div
              key={item.joint_name}
              className="flex items-center justify-between rounded-lg border px-3 py-2"
            >
              <span className="text-sm font-medium text-gray-700">
                {item.joint_name_ja}
              </span>
              <div className="flex items-center gap-3 text-sm">
                <span className="text-gray-500">
                  {item.user_angle.toFixed(1)}° / {item.ideal_angle.toFixed(1)}°
                </span>
                <span className="text-gray-400">差: {item.difference.toFixed(1)}°</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${RATING_STYLES[item.rating]}`}
                >
                  {RATING_LABELS[item.rating]}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
