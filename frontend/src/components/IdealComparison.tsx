"use client";

/**
 * 理想フォームとの比較表示コンポーネント.
 *
 * TODO: 実装内容
 * - 左右分割: ユーザーのスケルトン vs 理想スケルトン
 * - 差分が大きい関節をハイライト
 * - アニメーション再生で動的比較
 */

import type { IdealComparison as IdealComparisonType } from "@/types/analysis";

interface Props {
  comparisons: IdealComparisonType[];
}

export function IdealComparison({ comparisons }: Props) {
  // CoachingPanel 内に統合済み。
  // 将来的にスケルトンの並列表示を実装する場合はここに配置。
  return null;
}
