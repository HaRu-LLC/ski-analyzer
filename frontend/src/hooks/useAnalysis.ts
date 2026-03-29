import { useCallback, useEffect, useState } from "react";
import { getAnalysisStatus, getAnalysisResult } from "@/utils/api";
import type { AnalysisResult, AnalysisStatus } from "@/types/analysis";

interface UseAnalysisOptions {
  analysisId: string;
  pollingInterval?: number;
}

/**
 * 解析状況ポーリングと結果取得フック.
 */
export function useAnalysis({
  analysisId,
  pollingInterval = 2000,
}: UseAnalysisOptions) {
  const [status, setStatus] = useState<AnalysisStatus>("validating");
  const [progress, setProgress] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        // ポーリング失敗は無視
      }
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [analysisId, status, pollingInterval]);

  const retry = useCallback(() => {
    setStatus("validating");
    setProgress(0);
    setError(null);
  }, []);

  return { status, progress, eta, result, error, retry };
}
