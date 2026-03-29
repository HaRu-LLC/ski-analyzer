"""アップロード関連のスキーマ."""

from pydantic import BaseModel, Field


class VideoValidationResult(BaseModel):
    """動画バリデーション結果."""

    width: int
    height: int
    fps: float
    duration: float = Field(description="動画長（秒）")
    total_frames: int

    @property
    def is_hd(self) -> bool:
        """1080p以上か."""
        return min(self.width, self.height) >= 1080
