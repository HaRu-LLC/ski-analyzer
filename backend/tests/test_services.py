"""バックエンドのユニットテスト."""

from app.services.angle_calculator import AngleCalculator
from app.services.ideal_comparator import IdealComparator
from app.services.pose_estimator import TARGET_JOINTS, PoseEstimator


class TestAngleCalculator:
    """AngleCalculator のテスト."""

    def test_axis_angle_to_euler_zero(self):
        """ゼロ回転の変換."""
        result = AngleCalculator.axis_angle_to_euler([0.0, 0.0, 0.0])
        assert result["flexion"] == 0.0
        assert result["rotation"] == 0.0
        assert result["abduction"] == 0.0

    def test_axis_angle_to_euler_nonzero(self):
        """非ゼロ回転の変換."""
        result = AngleCalculator.axis_angle_to_euler([0.5, 0.3, 0.1])
        assert isinstance(result["flexion"], float)
        assert isinstance(result["rotation"], float)
        assert isinstance(result["abduction"], float)

    def test_calculate_frame_angles(self):
        """1フレームの角度算出."""
        mock_pose = {
            "joint_positions_3d": {name: [0.0, 0.0, 0.0] for name in TARGET_JOINTS},
            "joint_rotations": {name: [0.1, 0.2, 0.3] for name in TARGET_JOINTS},
        }
        angles = AngleCalculator.calculate_frame_angles(mock_pose)
        assert len(angles) == len(TARGET_JOINTS)
        for angle in angles:
            assert "joint_name" in angle
            assert "joint_name_ja" in angle
            assert "confidence" in angle

    def test_calculate_video_angles(self):
        """動画全体の角度算出."""
        mock_poses = [
            {
                "joint_positions_3d": {name: [0.0, 0.0, 0.0] for name in TARGET_JOINTS},
                "joint_rotations": {name: [0.1 * i, 0.2, 0.3] for name in TARGET_JOINTS},
            }
            for i in range(10)
        ]
        result = AngleCalculator.calculate_video_angles(mock_poses, fps=60.0)
        assert len(result) == 10
        assert result[0]["frame_index"] == 0
        assert result[0]["timestamp_ms"] == 0.0
        assert result[5]["frame_index"] == 5


class TestPoseEstimator:
    """PoseEstimator のテスト（モックモード）."""

    def test_mock_data_structure(self):
        """モックデータの構造確認."""
        estimator = PoseEstimator(use_mock=True)
        result = estimator._generate_mock_data()
        assert "joint_positions_3d" in result
        assert "joint_rotations" in result
        assert "smpl_params" in result
        assert len(result["smpl_params"]["betas"]) == 10
        assert len(result["smpl_params"]["body_pose"]) == 69


class TestIdealComparator:
    """IdealComparator のテスト."""

    def test_compare_perfect_form(self):
        """理想と一致する場合."""
        comparator = IdealComparator()
        summary = {
            "左膝": {"flexion": {"mean": -55.0, "min": -60.0, "max": -50.0, "std": 3.0}},
            "右膝": {"flexion": {"mean": -55.0, "min": -60.0, "max": -50.0, "std": 3.0}},
        }
        result = comparator.compare(summary)
        for item in result:
            if item["joint_name"] in ("左膝", "右膝"):
                assert item["rating"] == "good"

    def test_compare_poor_form(self):
        """理想から大きく外れた場合."""
        comparator = IdealComparator()
        summary = {
            "左膝": {"flexion": {"mean": -10.0, "min": -15.0, "max": -5.0, "std": 3.0}},
        }
        result = comparator.compare(summary)
        assert len(result) >= 1
        assert result[0]["rating"] == "poor"

    def test_compare_sorted_by_difference(self):
        """差分が大きい順にソートされる."""
        comparator = IdealComparator()
        summary = {
            "左膝": {"flexion": {"mean": -50.0, "min": -55.0, "max": -45.0, "std": 3.0}},
            "右膝": {"flexion": {"mean": -10.0, "min": -15.0, "max": -5.0, "std": 3.0}},
        }
        result = comparator.compare(summary)
        assert len(result) == 2
        assert result[0]["difference"] >= result[1]["difference"]
