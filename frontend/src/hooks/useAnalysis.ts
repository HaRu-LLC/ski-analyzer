import { useCallback, useEffect, useRef, useState } from "react";
import { getAnalysisStatus, getAnalysisResult } from "@/utils/api";
import type { AnalysisResult, AnalysisStatus } from "@/types/analysis";

const RESULT_READY_STATUSES: AnalysisStatus[] = [
  "saving_results",
  "rendering_overlay",
  "generating_report",
  "completed",
];

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
  const [retryToken, setRetryToken] = useState(0);
  const resultRefreshInFlightRef = useRef<Promise<void> | null>(null);
  const resultRef = useRef<AnalysisResult | null>(null);
  const statusRef = useRef<AnalysisStatus>("validating");
  const hasCompletedResultRef = useRef(false);

  useEffect(() => {
    resultRef.current = result;
  }, [result]);

  useEffect(() => {
    statusRef.current = "validating";
    hasCompletedResultRef.current = false;
    resultRef.current = null;
    setStatus("validating");
    setProgress(0);
    setEta(null);
    setResult(null);
    setError(null);
    resultRefreshInFlightRef.current = null;
  }, [analysisId, retryToken]);

  useEffect(() => {
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const stopPolling = () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };

    const markCompleted = () => {
      hasCompletedResultRef.current = true;
      stopPolling();
    };

    const refreshResult = (nextStatus: AnalysisStatus) => {
      if (resultRefreshInFlightRef.current) {
        return resultRefreshInFlightRef.current;
      }

      let refreshPromise: Promise<void> | null = null;
      refreshPromise = (async () => {
        try {
          const analysisResult = await getAnalysisResult(analysisId);
          if (cancelled) return;
          resultRef.current = analysisResult;
          setResult(analysisResult);
          if (nextStatus === "completed") {
            markCompleted();
          }
        } catch {
          // result.json 作成前や一時的な取得失敗時は次回ポーリングで再試行
        } finally {
          if (resultRefreshInFlightRef.current === refreshPromise) {
            resultRefreshInFlightRef.current = null;
          }
        }
      })();

      resultRefreshInFlightRef.current = refreshPromise;
      return refreshPromise;
    };

    const poll = async () => {
      if (cancelled || hasCompletedResultRef.current || statusRef.current === "failed") {
        stopPolling();
        return;
      }

      try {
        const res = await getAnalysisStatus(analysisId);
        if (cancelled) return;
        const hasCurrentResult = resultRef.current?.analysis_id === analysisId;

        setProgress(res.progress);
        setEta(res.estimated_remaining_seconds);
        statusRef.current = res.status;
        setStatus(res.status);

        if (hasCurrentResult && resultRef.current) {
          const nextResult = {
            ...resultRef.current,
            artifacts: res.artifacts,
          };
          resultRef.current = nextResult;
          setResult((current) =>
            current
              ? {
                  ...current,
                  artifacts: res.artifacts,
                }
              : current
          );
        }

        if (RESULT_READY_STATUSES.includes(res.status) && !hasCurrentResult) {
          void refreshResult(res.status);
        } else if (res.status === "completed" && hasCurrentResult) {
          markCompleted();
        }

        if (res.status === "failed") {
          stopPolling();
          setError(res.error_message || "解析に失敗しました");
        }
      } catch {
        // ポーリング失敗は無視
      }
    };

    void poll();
    intervalId = setInterval(() => {
      void poll();
    }, pollingInterval);

    return () => {
      cancelled = true;
      stopPolling();
    };
  }, [analysisId, pollingInterval, retryToken]);

  const retry = useCallback(() => {
    statusRef.current = "validating";
    hasCompletedResultRef.current = false;
    resultRef.current = null;
    setStatus("validating");
    setProgress(0);
    setError(null);
    setResult(null);
    setEta(null);
    resultRefreshInFlightRef.current = null;
    setRetryToken((current) => current + 1);
  }, []);

  return { status, progress, eta, result, error, retry };
}
