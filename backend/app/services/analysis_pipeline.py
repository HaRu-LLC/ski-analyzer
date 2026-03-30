"""解析パイプラインサービス: フレーム抽出からレポート生成まで一気通貫で実行."""

import csv
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core import settings
from app.services.angle_calculator import AngleCalculator
from app.services.coaching_generator import CoachingGenerator
from app.services.ideal_comparator import IdealComparator
from app.services.pose_estimator import PoseEstimator
from app.services.report_generator import ReportGenerator
from app.services.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

# モックモード時に生成するフレーム数
MOCK_FRAME_COUNT = 10


class AnalysisPipeline:
    """解析パイプライン全体を統合的に実行する.

    フレーム抽出 → ポーズ推定 → 角度算出 → コーチング生成 →
    理想フォーム比較 → 結果保存（JSON/CSV）→ レポート生成の順に処理する。
    """

    def __init__(self, use_mock: bool = False):
        """パイプラインを初期化する.

        Args:
            use_mock: モックモードで実行するかどうか
        """
        self.use_mock = use_mock

    def run(
        self,
        video_path: Path,
        output_dir: Path,
        fps: float,
        analysis_id: str = "",
        video_info: dict[str, Any] | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, Any]:
        """解析パイプライン全体を実行する.

        Args:
            video_path: 入力動画ファイルパス
            output_dir: 解析結果の出力ディレクトリ
            fps: 動画のフレームレート
            analysis_id: 解析ID (結果JSONに含める)
            video_info: 動画メタ情報 (width, height, duration 等)
            progress_callback: 進捗通知コールバック (stage, percent) -> None

        Returns:
            解析結果全体を格納したdict
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        def _notify(stage: str, percent: float) -> None:
            if progress_callback:
                progress_callback(stage, percent)

        # ----------------------------------------------------------
        # 1. フレーム抽出
        # ----------------------------------------------------------
        _notify("extracting_frames", 0.0)

        if self.use_mock:
            # モックモードではフレーム抽出をスキップし、ダミーパスを生成
            frame_paths = [output_dir / f"frame_{i:06d}.jpg" for i in range(MOCK_FRAME_COUNT)]
            logger.info("Mock mode: generated %d dummy frame paths", len(frame_paths))
        else:
            frames_dir = output_dir / "frames"
            frame_paths = VideoProcessor.extract_frames(video_path, frames_dir)
            logger.info("Extracted %d frames", len(frame_paths))

        _notify("extracting_frames", 100.0)

        # ----------------------------------------------------------
        # 2. ポーズ推定
        # ----------------------------------------------------------
        _notify("estimating_pose", 0.0)

        # モックモードが要求されていてシングルトンと異なる場合は
        # 専用インスタンスを生成する（グローバル設定を変更しない）
        if self.use_mock and not settings.use_mock:
            estimator = PoseEstimator(use_mock=True)
        else:
            estimator = PoseEstimator.get_instance()
        pose_results = estimator.estimate_video(frame_paths)

        logger.info("Pose estimation completed for %d frames", len(pose_results))
        _notify("estimating_pose", 100.0)

        # ----------------------------------------------------------
        # 3. 関節角度算出
        # ----------------------------------------------------------
        _notify("calculating_angles", 0.0)

        frame_data_list = AngleCalculator.calculate_video_angles(pose_results, fps)

        logger.info("Angle calculation completed for %d frames", len(frame_data_list))
        _notify("calculating_angles", 100.0)

        # ----------------------------------------------------------
        # 4. 角度要約 + コーチング生成
        # ----------------------------------------------------------
        _notify("generating_coaching", 0.0)

        angle_summary = CoachingGenerator.summarize_angles(frame_data_list)
        coaching_gen = CoachingGenerator()
        coaching = coaching_gen.generate(angle_summary)

        logger.info("Coaching generation completed")
        _notify("generating_coaching", 100.0)

        # ----------------------------------------------------------
        # 5. 理想フォーム比較
        # ----------------------------------------------------------
        _notify("comparing_ideal", 0.0)

        comparator = IdealComparator()
        ideal_comparison = comparator.compare(angle_summary)

        logger.info("Ideal comparison completed")
        _notify("comparing_ideal", 100.0)

        # ----------------------------------------------------------
        # 6. 結果dictの組み立て
        # ----------------------------------------------------------
        base_video_info = video_info or {}
        result: dict[str, Any] = {
            "analysis_id": analysis_id,
            "video_info": {
                **base_video_info,
                "fps": fps,
                "total_frames": len(frame_paths),
            },
            "total_frames": len(frame_data_list),
            "frames": frame_data_list,
            "angle_summary": angle_summary,
            "coaching": coaching,
            "ideal_comparison": ideal_comparison,
        }

        # ----------------------------------------------------------
        # 7. result.json の保存
        # ----------------------------------------------------------
        _notify("saving_results", 0.0)

        result_json_path = output_dir / "result.json"
        result_json_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Saved result.json to %s", result_json_path)

        # ----------------------------------------------------------
        # 8. angles.csv の保存
        # ----------------------------------------------------------
        csv_path = output_dir / "angles.csv"
        self._save_angles_csv(frame_data_list, csv_path)
        logger.info("Saved angles.csv to %s", csv_path)

        _notify("saving_results", 100.0)

        # ----------------------------------------------------------
        # 9. オーバーレイ動画レンダリング（モック時はスキップ）
        # ----------------------------------------------------------
        if not self.use_mock:
            _notify("rendering_overlay", 0.0)
            # TODO: OverlayRenderer の実装後に有効化
            logger.info("Overlay rendering skipped (not yet implemented)")
            _notify("rendering_overlay", 100.0)

        # ----------------------------------------------------------
        # 10. PDFレポート生成（モック時はスキップ）
        # ----------------------------------------------------------
        if not self.use_mock:
            _notify("generating_report", 0.0)
            report_path = output_dir / "report.pdf"
            ReportGenerator.generate(result, report_path)
            logger.info("Report generated at %s", report_path)
            _notify("generating_report", 100.0)

        _notify("completed", 100.0)
        return result

    @staticmethod
    def _save_angles_csv(frame_data_list: list[dict], csv_path: Path) -> None:
        """フレーム別の関節角度データをCSVとして保存する.

        Args:
            frame_data_list: AngleCalculator.calculate_video_angles() の出力
            csv_path: 出力CSVパス
        """
        fieldnames = [
            "frame_index",
            "timestamp_ms",
            "joint_name",
            "joint_name_ja",
            "flexion",
            "rotation",
            "abduction",
            "confidence",
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for frame in frame_data_list:
                for angle in frame.get("joint_angles", []):
                    writer.writerow(
                        {
                            "frame_index": frame["frame_index"],
                            "timestamp_ms": frame["timestamp_ms"],
                            "joint_name": angle["joint_name"],
                            "joint_name_ja": angle["joint_name_ja"],
                            "flexion": angle["flexion"],
                            "rotation": angle["rotation"],
                            "abduction": angle["abduction"],
                            "confidence": angle["confidence"],
                        }
                    )
