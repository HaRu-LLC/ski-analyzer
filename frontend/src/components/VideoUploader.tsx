"use client";

import { useCallback, useState } from "react";

interface Props {
  onUpload: (file: File) => void;
  uploading: boolean;
}

const ALLOWED_TYPES = ["video/mp4", "video/quicktime", "video/webm"];
const MAX_SIZE = 500 * 1024 * 1024; // 500MB

export function VideoUploader({ onUpload, uploading }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return "対応形式: MP4 / MOV / WebM";
    }
    if (file.size > MAX_SIZE) {
      return `ファイルサイズが上限（500MB）を超えています（${(file.size / 1024 / 1024).toFixed(0)}MB）`;
    }
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) {
        setValidationError(err);
        return;
      }
      setValidationError(null);
      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="w-full max-w-xl">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center gap-4 rounded-2xl border-2 border-dashed p-12 transition-colors ${
          dragOver
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50"
        } ${uploading ? "pointer-events-none opacity-60" : ""}`}
      >
        <div className="text-5xl">📤</div>
        <div className="text-center">
          <p className="text-lg font-medium text-gray-700">
            {uploading ? "アップロード中..." : "動画をドラッグ&ドロップ"}
          </p>
          <p className="mt-1 text-sm text-gray-500">
            またはクリックしてファイルを選択
          </p>
        </div>
        <input
          type="file"
          accept="video/mp4,video/quicktime,video/webm"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
          disabled={uploading}
        />
        {uploading && (
          <div className="h-1.5 w-48 overflow-hidden rounded-full bg-gray-200">
            <div className="h-full animate-pulse rounded-full bg-blue-500" style={{ width: "60%" }} />
          </div>
        )}
      </label>
      {validationError && (
        <p className="mt-2 text-center text-sm text-red-600">{validationError}</p>
      )}
    </div>
  );
}
