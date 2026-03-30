/** 解析ステータス */
export type AnalysisStatus =
  | "uploading"
  | "validating"
  | "extracting_frames"
  | "estimating_pose"
  | "calculating_angles"
  | "generating_coaching"
  | "comparing_ideal"
  | "saving_results"
  | "rendering_overlay"
  | "generating_report"
  | "completed"
  | "failed";

/** 関節角度データ */
export interface JointAngle {
  joint_name: string;
  joint_name_ja: string;
  flexion: number | null;
  rotation: number | null;
  abduction: number | null;
  confidence: "high" | "medium" | "low";
}

/** 1フレームの解析データ */
export interface FrameData {
  frame_index: number;
  timestamp_ms: number;
  joint_positions_3d: Record<string, [number, number, number]>;
  joint_rotations: Record<string, [number, number, number]>;
  joint_angles: JointAngle[];
}

/** AIコーチングアドバイス */
export interface CoachingAdvice {
  overall_score: number;
  summary: string;
  details: {
    joint: string;
    advice: string;
    reason?: string;
    exercise?: string;
    priority: "high" | "medium" | "low";
  }[];
}

/** 理想フォーム比較 */
export interface IdealComparison {
  joint_name: string;
  joint_name_ja: string;
  user_angle: number;
  ideal_angle: number;
  difference: number;
  rating: "good" | "needs_improvement" | "poor";
}

/** 解析結果全体 */
export interface AnalysisResult {
  analysis_id: string;
  video_info: {
    width: number;
    height: number;
    fps: number;
    duration: number;
    total_frames: number;
  };
  total_frames: number;
  frames: FrameData[];
  coaching: CoachingAdvice;
  ideal_comparison: IdealComparison[];
}

/** 解析状況レスポンス */
export interface StatusResponse {
  analysis_id: string;
  status: AnalysisStatus;
  progress: number;
  estimated_remaining_seconds: number | null;
  error_message: string | null;
}

/** アップロードレスポンス */
export interface UploadResponse {
  analysis_id: string;
  status: AnalysisStatus;
  message: string;
}
