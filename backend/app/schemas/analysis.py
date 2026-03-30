"""API リクエスト/レスポンススキーマ."""

from enum import StrEnum

from pydantic import BaseModel, Field


class AnalysisStatus(StrEnum):
    """解析ステータス."""

    UPLOADING = "uploading"
    VALIDATING = "validating"
    EXTRACTING_FRAMES = "extracting_frames"
    ESTIMATING_POSE = "estimating_pose"
    CALCULATING_ANGLES = "calculating_angles"
    GENERATING_COACHING = "generating_coaching"
    COMPARING_IDEAL = "comparing_ideal"
    SAVING_RESULTS = "saving_results"
    RENDERING_OVERLAY = "rendering_overlay"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """アップロードレスポンス."""

    analysis_id: str
    status: AnalysisStatus
    message: str


class AnalysisArtifacts(BaseModel):
    """生成済み成果物の可用性."""

    video: bool = False
    report: bool = False
    csv: bool = False


class StatusResponse(BaseModel):
    """解析状況レスポンス."""

    analysis_id: str
    status: AnalysisStatus
    progress: float = Field(ge=0, le=100, description="進捗率 (%)")
    estimated_remaining_seconds: int | None = None
    error_message: str | None = None
    artifacts: AnalysisArtifacts = Field(default_factory=AnalysisArtifacts)


class JointAngle(BaseModel):
    """単一関節の角度データ."""

    joint_name: str
    joint_name_ja: str
    flexion: float | None = Field(None, description="屈曲/伸展 (度)")
    rotation: float | None = Field(None, description="内旋/外旋 (度)")
    abduction: float | None = Field(None, description="外転/内転 (度)")
    confidence: str = Field(description="精度レベル: high / medium / low")


class FrameData(BaseModel):
    """1フレームの解析データ."""

    frame_index: int
    timestamp_ms: float
    joint_positions_3d: dict[str, list[float]]  # joint_name -> [x, y, z]
    joint_rotations: dict[str, list[float]]  # joint_name -> [rx, ry, rz] axis-angle
    joint_angles: list[JointAngle]


class CoachingAdvice(BaseModel):
    """AIコーチングアドバイス."""

    overall_score: int = Field(ge=0, le=100)
    summary: str
    details: list[dict[str, str]]  # {"joint": "膝", "advice": "...", "priority": "high"}


class IdealComparison(BaseModel):
    """理想フォームとの比較."""

    joint_name: str
    joint_name_ja: str
    user_angle: float
    ideal_angle: float
    difference: float
    rating: str  # "good" / "needs_improvement" / "poor"


class AnalysisResult(BaseModel):
    """解析結果全体."""

    analysis_id: str
    video_info: dict  # fps, duration, resolution等
    total_frames: int
    frames: list[FrameData]
    coaching: CoachingAdvice
    ideal_comparison: list[IdealComparison]
    artifacts: AnalysisArtifacts = Field(default_factory=AnalysisArtifacts)
