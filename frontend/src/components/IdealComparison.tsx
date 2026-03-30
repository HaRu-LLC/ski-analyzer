"use client";

import type { IdealComparison as IdealComparisonType } from "@/types/analysis";

type Rating = IdealComparisonType["rating"];

interface Props {
  comparisons: IdealComparisonType[];
}

const RATING_STYLES: Record<Rating, { bg: string; text: string; label: string }> = {
  good: { bg: "bg-green-900/30", text: "text-green-400", label: "良好" },
  needs_improvement: { bg: "bg-yellow-900/30", text: "text-yellow-400", label: "改善余地" },
  poor: { bg: "bg-red-900/30", text: "text-red-400", label: "要改善" },
};

export function IdealComparison({ comparisons }: Props) {
  if (comparisons.length === 0) {
    return (
      <div className="rounded-xl border bg-gray-900 p-4 text-sm text-gray-400">
        比較データがありません
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-gray-900 p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold text-gray-200">
        理想フォームとの比較
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">理想フォームとの比較</caption>
          <thead>
            <tr className="border-b border-gray-700 text-left text-gray-400">
              <th scope="col" className="pb-2 pr-3">部位</th>
              <th scope="col" className="pb-2 pr-3 text-right">実測値</th>
              <th scope="col" className="pb-2 pr-3 text-right">理想値</th>
              <th scope="col" className="pb-2 pr-3 text-right">差分</th>
              <th scope="col" className="pb-2">評価</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map((c) => {
              const style = RATING_STYLES[c.rating] ?? { bg: "bg-gray-900/30", text: "text-gray-400", label: "不明" };
              return (
                <tr key={c.joint_name} className="border-b border-gray-800">
                  <td className="py-2 pr-3 text-gray-200">{c.joint_name_ja}</td>
                  <td className="py-2 pr-3 text-right font-mono text-gray-300">
                    {c.user_angle.toFixed(1)}°
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-gray-400">
                    {c.ideal_angle.toFixed(1)}°
                  </td>
                  <td className="py-2 pr-3 text-right font-mono text-gray-300">
                    {c.difference.toFixed(1)}°
                  </td>
                  <td className="py-2">
                    <span
                      className={`inline-block rounded px-2 py-0.5 text-xs ${style.bg} ${style.text}`}
                    >
                      {style.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
