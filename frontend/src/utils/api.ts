/** バックエンドAPIクライアント */

import type { AnalysisResult, StatusResponse, UploadResponse } from "@/types/analysis";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || "エラーが発生しました");
  }
  return res.json();
}

/** 動画をアップロードして解析を開始 */
export async function uploadVideo(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "アップロードに失敗しました" }));
    throw new ApiError(res.status, body.detail);
  }
  return res.json();
}

/** 解析状況を確認 */
export async function getAnalysisStatus(id: string): Promise<StatusResponse> {
  return request(`/analysis/${id}/status`);
}

/** 解析結果を取得 */
export async function getAnalysisResult(id: string): Promise<AnalysisResult> {
  return request(`/analysis/${id}/result`);
}

/** フレーム別データを取得 */
export async function getFrameData(id: string, frameIndex: number) {
  return request(`/analysis/${id}/frames/${frameIndex}`);
}

/** ダウンロードURL生成 */
export function getDownloadUrl(id: string, type: "video" | "report" | "csv"): string {
  return `${API_BASE}/api/download/${id}/${type}`;
}
