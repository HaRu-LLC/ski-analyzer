"""APIルート用の依存性注入."""

from app.services.coaching_generator import CoachingGenerator
from app.services.ideal_comparator import IdealComparator
from app.services.pose_estimator import PoseEstimator


def get_pose_estimator() -> PoseEstimator:
    """PoseEstimator シングルトンを取得する."""
    return PoseEstimator.get_instance()


def get_coaching_generator() -> CoachingGenerator:
    """CoachingGenerator インスタンスを取得する."""
    return CoachingGenerator()


def get_ideal_comparator() -> IdealComparator:
    """IdealComparator インスタンスを取得する."""
    return IdealComparator()
