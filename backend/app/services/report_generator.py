"""PDFレポート生成サービス."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """解析結果をPDFレポートとして出力する.

    TODO: reportlab + matplotlib で実装
    - 表紙（解析日時、動画情報）
    - 総合スコア
    - 部位別の関節角度サマリー
    - 時系列グラフ（主要関節）
    - 理想フォームとの比較表
    - AIコーチングアドバイス
    """

    @staticmethod
    def generate(
        analysis_result: dict,
        output_path: Path,
    ) -> Path:
        """PDFレポートを生成する.

        Args:
            analysis_result: 解析結果全体
            output_path: 出力PDFパス

        Returns:
            生成されたPDFパス
        """
        # TODO: 実装
        logger.info("Report generation not yet implemented: %s", output_path)
        return output_path
