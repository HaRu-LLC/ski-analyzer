"""カスタム例外定義."""


class SkiAnalyzerError(Exception):
    """基底例外クラス."""


class VideoValidationError(SkiAnalyzerError):
    """動画バリデーションエラー."""


class AnalysisNotFoundError(SkiAnalyzerError):
    """解析結果が見つからない."""


class PoseEstimationError(SkiAnalyzerError):
    """姿勢推定エラー."""


class ModelNotLoadedError(SkiAnalyzerError):
    """モデル未ロードエラー."""
