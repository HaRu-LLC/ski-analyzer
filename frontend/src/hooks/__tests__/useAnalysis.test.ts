import { act, renderHook, waitFor } from "@testing-library/react";
import { useAnalysis } from "../useAnalysis";
import type { AnalysisResult, StatusResponse } from "@/types/analysis";

jest.mock("@/utils/api", () => ({
  getAnalysisStatus: jest.fn(),
  getAnalysisResult: jest.fn(),
}));

const { getAnalysisStatus, getAnalysisResult } = jest.requireMock("@/utils/api") as {
  getAnalysisStatus: jest.Mock;
  getAnalysisResult: jest.Mock;
};

function makeStatus(
  status: StatusResponse["status"],
  artifacts: StatusResponse["artifacts"],
): StatusResponse {
  return {
    analysis_id: "analysis-a",
    status,
    progress: 100,
    estimated_remaining_seconds: null,
    error_message: null,
    artifacts,
  };
}

function makeResult(
  analysisId: string,
  artifacts: AnalysisResult["artifacts"],
): AnalysisResult {
  return {
    analysis_id: analysisId,
    video_info: {
      width: 1920,
      height: 1080,
      fps: 30,
      duration: 1,
      total_frames: 10,
    },
    total_frames: 10,
    frames: [],
    coaching: {
      overall_score: 80,
      summary: "ok",
      details: [],
    },
    ideal_comparison: [],
    artifacts,
  };
}

describe("useAnalysis", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("fetches the full result only once and updates artifacts from status polling", async () => {
    const statuses = [
      makeStatus("saving_results", { video: false, report: false, csv: true }),
      makeStatus("generating_report", { video: false, report: false, csv: true }),
      makeStatus("completed", { video: true, report: true, csv: true }),
    ];
    let statusCall = 0;
    getAnalysisStatus.mockImplementation(() =>
      Promise.resolve(statuses[Math.min(statusCall++, statuses.length - 1)])
    );
    getAnalysisResult.mockResolvedValue(
      makeResult("analysis-a", { video: false, report: false, csv: true })
    );

    const { result } = renderHook(() =>
      useAnalysis({ analysisId: "analysis-a", pollingInterval: 10 })
    );

    await waitFor(() => expect(result.current.result?.analysis_id).toBe("analysis-a"));
    expect(getAnalysisResult).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(30);
    });

    await waitFor(() =>
      expect(result.current.result?.artifacts).toEqual({
        video: true,
        report: true,
        csv: true,
      })
    );
    expect(getAnalysisResult).toHaveBeenCalledTimes(1);
  });

  it("refetches for a new analysisId even if the previous result is already loaded", async () => {
    const statusById: Record<string, StatusResponse> = {
      "analysis-a": makeStatus("completed", { video: true, report: true, csv: true }),
      "analysis-b": {
        ...makeStatus("completed", { video: false, report: true, csv: true }),
        analysis_id: "analysis-b",
      },
    };
    getAnalysisStatus.mockImplementation((analysisId: string) =>
      Promise.resolve(statusById[analysisId])
    );
    getAnalysisResult.mockImplementation((analysisId: string) =>
      Promise.resolve(
        makeResult(analysisId, statusById[analysisId].artifacts)
      )
    );

    const { result, rerender } = renderHook(
      ({ analysisId }) => useAnalysis({ analysisId, pollingInterval: 10 }),
      { initialProps: { analysisId: "analysis-a" } }
    );

    await waitFor(() => expect(result.current.result?.analysis_id).toBe("analysis-a"));

    rerender({ analysisId: "analysis-b" });

    await waitFor(() => expect(result.current.result?.analysis_id).toBe("analysis-b"));
    expect(result.current.result?.artifacts.video).toBe(false);
    expect(getAnalysisResult).toHaveBeenCalledTimes(2);
  });

  it("keeps an in-flight result fetch alive across status changes", async () => {
    const statuses = [
      makeStatus("saving_results", { video: false, report: false, csv: true }),
      makeStatus("completed", { video: true, report: true, csv: true }),
    ];
    let statusCall = 0;
    getAnalysisStatus.mockImplementation(() =>
      Promise.resolve(statuses[Math.min(statusCall++, statuses.length - 1)])
    );

    let resolveResult: ((value: AnalysisResult) => void) | null = null;
    getAnalysisResult.mockImplementation(
      () =>
        new Promise<AnalysisResult>((resolve) => {
          resolveResult = resolve;
        })
    );

    const { result } = renderHook(() =>
      useAnalysis({ analysisId: "analysis-a", pollingInterval: 10 })
    );

    await act(async () => {
      jest.advanceTimersByTime(20);
    });

    expect(getAnalysisResult).toHaveBeenCalledTimes(1);
    expect(result.current.result).toBeNull();

    await act(async () => {
      resolveResult?.(makeResult("analysis-a", { video: false, report: false, csv: true }));
      await Promise.resolve();
      jest.advanceTimersByTime(20);
    });

    await waitFor(() =>
      expect(result.current.result?.artifacts).toEqual({
        video: true,
        report: true,
        csv: true,
      })
    );
    expect(getAnalysisResult).toHaveBeenCalledTimes(1);
  });

  it("restarts polling when retry is called after failure", async () => {
    const failedStatus = {
      ...makeStatus("failed", { video: false, report: false, csv: false }),
      error_message: "boom",
    };
    const completedStatus = makeStatus("completed", {
      video: true,
      report: true,
      csv: true,
    });

    getAnalysisStatus
      .mockResolvedValueOnce(failedStatus)
      .mockResolvedValue(completedStatus);
    getAnalysisResult.mockResolvedValue(
      makeResult("analysis-a", { video: true, report: true, csv: true })
    );

    const { result } = renderHook(() =>
      useAnalysis({ analysisId: "analysis-a", pollingInterval: 10 })
    );

    await waitFor(() => expect(result.current.error).toBe("boom"));

    await act(async () => {
      result.current.retry();
      await Promise.resolve();
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => expect(result.current.result?.analysis_id).toBe("analysis-a"));
    expect(result.current.error).toBeNull();
    expect(getAnalysisStatus.mock.calls.length).toBeGreaterThanOrEqual(2);
    expect(getAnalysisResult.mock.calls.length).toBeGreaterThanOrEqual(1);
  });
});
