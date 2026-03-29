"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { VideoUploader } from "@/components/VideoUploader";
import { uploadVideo } from "@/utils/api";

export default function HomePage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setError(null);
    setUploading(true);
    try {
      const res = await uploadVideo(file);
      router.push(`/analyze/${res.analysis_id}`);
    } catch (e: any) {
      setError(e.message || "アップロードに失敗しました");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-8 py-12">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-blue-900">
          スキーフォームをAIが解析
        </h2>
        <p className="mt-2 text-gray-600">
          動画をアップロードするだけで、関節角度の分析と改善アドバイスを提供します
        </p>
      </div>

      <VideoUploader onUpload={handleUpload} uploading={uploading} />

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* 撮影ガイド */}
      <div className="mt-8 max-w-2xl rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">📹 撮影ガイド</h3>
        <div className="grid grid-cols-1 gap-3 text-sm text-gray-600 sm:grid-cols-2">
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>正面から三脚で固定撮影</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>全身が画面の60〜70%に収まる距離</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>1080p以上、60fps以上で撮影</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>半袖・短パンなど体のラインが分かる服装</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>1分以内の動画</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-blue-500">✓</span>
            <span>対応形式: MP4 / MOV / WebM</span>
          </div>
        </div>
      </div>
    </div>
  );
}
