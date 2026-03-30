"""PDFレポート生成サービス."""

import io
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# 日本語フォント登録: TTFを優先し、フォールバックでCIDフォントを使用
_TTF_CANDIDATES = [
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _register_japanese_font() -> str:
    """日本語フォントを登録して使用可能なフォント名を返す.

    TTFフォントを優先的に探索し、見つかればそれを登録する。
    見つからない場合はCIDフォント(HeiseiKakuGo-W5)にフォールバックする。

    Returns:
        登録されたフォント名
    """
    for ttf_path in _TTF_CANDIDATES:
        if Path(ttf_path).exists():
            try:
                font = TTFont("JapaneseTTF", ttf_path)
                pdfmetrics.registerFont(font)
                logger.info("Registered TTF Japanese font: %s", ttf_path)
                return "JapaneseTTF"
            except Exception:
                logger.debug("Failed to load TTF font: %s", ttf_path, exc_info=True)
                continue

    # フォールバック: CIDフォント
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5", isVertical=False))
        logger.info("Registered CID Japanese font: HeiseiKakuGo-W5")
        return "HeiseiKakuGo-W5"
    except Exception:
        logger.warning("Failed to register any Japanese font, using Helvetica")
        return "Helvetica"


_FONT_NAME = _register_japanese_font()


def _safe_get(data: dict, key: str, default: Any = None) -> Any:
    """辞書から安全に値を取得する.

    Args:
        data: 対象辞書
        key: キー名
        default: デフォルト値

    Returns:
        取得した値またはデフォルト値
    """
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def _build_styles() -> dict[str, ParagraphStyle]:
    """PDF用スタイル定義を構築する.

    Returns:
        スタイル名をキーとしたParagraphStyleの辞書
    """
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["title"] = ParagraphStyle(
        "JaTitle",
        parent=base["Title"],
        fontName=_FONT_NAME,
        fontSize=28,
        leading=36,
        spaceAfter=20,
    )
    styles["heading"] = ParagraphStyle(
        "JaHeading",
        parent=base["Heading1"],
        fontName=_FONT_NAME,
        fontSize=18,
        leading=24,
        spaceAfter=12,
        spaceBefore=16,
    )
    styles["subheading"] = ParagraphStyle(
        "JaSubheading",
        parent=base["Heading2"],
        fontName=_FONT_NAME,
        fontSize=14,
        leading=18,
        spaceAfter=8,
        spaceBefore=12,
    )
    styles["body"] = ParagraphStyle(
        "JaBody",
        parent=base["Normal"],
        fontName=_FONT_NAME,
        fontSize=10,
        leading=16,
        spaceAfter=6,
    )
    styles["small"] = ParagraphStyle(
        "JaSmall",
        parent=base["Normal"],
        fontName=_FONT_NAME,
        fontSize=8,
        leading=12,
        spaceAfter=4,
    )
    styles["score"] = ParagraphStyle(
        "JaScore",
        parent=base["Title"],
        fontName=_FONT_NAME,
        fontSize=48,
        leading=56,
        alignment=1,
        spaceAfter=10,
    )
    styles["center"] = ParagraphStyle(
        "JaCenter",
        parent=base["Normal"],
        fontName=_FONT_NAME,
        fontSize=12,
        leading=16,
        alignment=1,
        spaceAfter=6,
    )
    return styles


def _build_cover_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """表紙ページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Spacer(1, 80 * mm))
    elements.append(Paragraph("スキー解析レポート", styles["title"]))
    elements.append(Spacer(1, 20 * mm))

    analysis_id = _safe_get(analysis_result, "analysis_id", "N/A")
    video_info = _safe_get(analysis_result, "video_info", {})
    duration = _safe_get(video_info, "duration", 0)
    fps = _safe_get(video_info, "fps", 0)
    width = _safe_get(video_info, "width", 0)
    height = _safe_get(video_info, "height", 0)
    total_frames = _safe_get(analysis_result, "total_frames", 0)

    info_lines = [
        f"解析ID: {analysis_id}",
        f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
        f"動画時間: {duration:.1f}秒",
        f"フレームレート: {fps} fps",
        f"解像度: {width} x {height}",
        f"総フレーム数: {total_frames}",
    ]
    for line in info_lines:
        elements.append(Paragraph(line, styles["center"]))

    elements.append(PageBreak())
    return elements


def _build_score_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """総合スコアページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Paragraph("総合スコア", styles["heading"]))
    elements.append(Spacer(1, 20 * mm))

    coaching = _safe_get(analysis_result, "coaching", {})
    score = _safe_get(coaching, "overall_score", 0)
    summary = _safe_get(coaching, "summary", "")

    elements.append(Paragraph(f"{score}", styles["score"]))
    elements.append(Paragraph("/ 100 点", styles["center"]))
    elements.append(Spacer(1, 10 * mm))

    if summary:
        elements.append(Paragraph("サマリー", styles["subheading"]))
        elements.append(Paragraph(xml_escape(summary), styles["body"]))

    elements.append(PageBreak())
    return elements


def _build_angle_summary_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """関節角度サマリーページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Paragraph("関節角度サマリー", styles["heading"]))
    elements.append(Spacer(1, 5 * mm))

    frames = _safe_get(analysis_result, "frames", [])
    if not frames:
        elements.append(Paragraph("フレームデータがありません。", styles["body"]))
        elements.append(PageBreak())
        return elements

    # 各関節の平均角度を算出
    joint_stats: dict[str, dict[str, list[float]]] = {}
    for frame in frames:
        joint_angles = _safe_get(frame, "joint_angles", [])
        for ja in joint_angles:
            name_ja = _safe_get(ja, "joint_name_ja", "")
            if not name_ja:
                continue
            if name_ja not in joint_stats:
                joint_stats[name_ja] = {
                    "flexion": [],
                    "rotation": [],
                    "abduction": [],
                }
            for key in ("flexion", "rotation", "abduction"):
                val = _safe_get(ja, key, None)
                if val is not None:
                    joint_stats[name_ja][key].append(float(val))

    if not joint_stats:
        elements.append(Paragraph("関節角度データがありません。", styles["body"]))
        elements.append(PageBreak())
        return elements

    # テーブルヘッダー
    table_data = [["関節名", "屈曲(平均)", "回旋(平均)", "外転(平均)", "信頼度"]]

    # 信頼度は最初のフレームのものを使用
    first_frame_angles = _safe_get(frames[0], "joint_angles", [])
    confidence_map: dict[str, str] = {}
    for ja in first_frame_angles:
        name_ja = _safe_get(ja, "joint_name_ja", "")
        confidence_map[name_ja] = _safe_get(ja, "confidence", "N/A")

    for name_ja, stats in joint_stats.items():
        avg_flex = sum(stats["flexion"]) / len(stats["flexion"]) if stats["flexion"] else 0
        avg_rot = sum(stats["rotation"]) / len(stats["rotation"]) if stats["rotation"] else 0
        avg_abd = sum(stats["abduction"]) / len(stats["abduction"]) if stats["abduction"] else 0
        conf = confidence_map.get(name_ja, "N/A")
        table_data.append(
            [
                name_ja,
                f"{avg_flex:.1f}\u00b0",
                f"{avg_rot:.1f}\u00b0",
                f"{avg_abd:.1f}\u00b0",
                conf,
            ]
        )

    table = Table(table_data, colWidths=[80, 80, 80, 80, 60])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#D9E2F3")],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    elements.append(table)
    elements.append(PageBreak())
    return elements


def _build_timeseries_graph(analysis_result: dict) -> bytes | None:
    """時系列グラフを生成しPNGバイト列を返す.

    Args:
        analysis_result: 解析結果データ

    Returns:
        PNG画像バイト列。フレームデータが空の場合はNone
    """
    frames = _safe_get(analysis_result, "frames", [])
    if not frames:
        return None

    # 対象関節
    target_joints = ["左膝", "右膝", "左股関節", "右股関節", "左肩", "右肩"]

    # フレームごとの屈曲角度を収集
    timestamps: list[float] = []
    joint_data: dict[str, list[float]] = {j: [] for j in target_joints}

    for frame in frames:
        ts = _safe_get(frame, "timestamp_ms", 0.0)
        timestamps.append(float(ts) / 1000.0)  # ms -> s

        joint_angles = _safe_get(frame, "joint_angles", [])
        angle_map: dict[str, float] = {}
        for ja in joint_angles:
            name_ja = _safe_get(ja, "joint_name_ja", "")
            flexion_val = _safe_get(ja, "flexion", None)
            if name_ja in target_joints and flexion_val is not None:
                angle_map[name_ja] = float(flexion_val)

        for j in target_joints:
            joint_data[j].append(angle_map.get(j, math.nan))

    fig, ax = plt.subplots(figsize=(7, 4))

    try:
        line_styles = ["-", "-", "--", "--", "-.", "-."]
        line_colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
        ]

        for i, joint_name in enumerate(target_joints):
            if joint_data[joint_name]:
                ax.plot(
                    timestamps,
                    joint_data[joint_name],
                    label=joint_name,
                    linestyle=line_styles[i % len(line_styles)],
                    color=line_colors[i % len(line_colors)],
                    linewidth=1.5,
                )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Flexion (deg)")
        ax.set_title("Joint Angle Time Series")
        ax.legend(loc="best", fontsize=7)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        return buf.getvalue()
    finally:
        plt.close(fig)


def _build_graph_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """時系列グラフページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Paragraph("時系列グラフ", styles["heading"]))
    elements.append(Spacer(1, 5 * mm))

    graph_bytes = _build_timeseries_graph(analysis_result)
    if graph_bytes is None:
        elements.append(
            Paragraph(
                "フレームデータがないためグラフを生成できません。",
                styles["body"],
            ),
        )
    else:
        img_buf = io.BytesIO(graph_bytes)
        img = Image(img_buf, width=170 * mm, height=100 * mm)
        elements.append(img)

    elements.append(Spacer(1, 5 * mm))
    elements.append(
        Paragraph(
            "屈曲角度の時系列推移（膝・股関節・肩）",
            styles["small"],
        ),
    )
    elements.append(PageBreak())
    return elements


def _build_comparison_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """理想フォーム比較テーブルページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Paragraph("理想フォームとの比較", styles["heading"]))
    elements.append(Spacer(1, 5 * mm))

    comparisons = _safe_get(analysis_result, "ideal_comparison", [])
    if not comparisons:
        elements.append(Paragraph("比較データがありません。", styles["body"]))
        elements.append(PageBreak())
        return elements

    rating_labels = {
        "excellent": "優秀",
        "good": "良好",
        "needs_improvement": "要改善",
        "poor": "不良",
    }

    table_data = [["関節名", "計測角度", "理想角度", "差分", "評価"]]
    for comp in comparisons:
        name_ja = _safe_get(comp, "joint_name_ja", "N/A")
        user_angle = _safe_get(comp, "user_angle", 0)
        ideal_angle = _safe_get(comp, "ideal_angle", 0)
        diff = _safe_get(comp, "difference", 0)
        rating_raw = _safe_get(comp, "rating", "N/A")
        rating = rating_labels.get(rating_raw, rating_raw)
        table_data.append(
            [
                name_ja,
                f"{user_angle:.1f}\u00b0",
                f"{ideal_angle:.1f}\u00b0",
                f"{diff:.1f}\u00b0",
                rating,
            ]
        )

    table = Table(table_data, colWidths=[80, 70, 70, 60, 70])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#D9E2F3")],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    elements.append(table)
    elements.append(PageBreak())
    return elements


def _build_coaching_page(
    analysis_result: dict,
    styles: dict[str, ParagraphStyle],
) -> list:
    """AIコーチングアドバイスページの要素を構築する.

    Args:
        analysis_result: 解析結果データ
        styles: スタイル辞書

    Returns:
        Flowable要素のリスト
    """
    elements: list = []
    elements.append(Paragraph("AIコーチングアドバイス", styles["heading"]))
    elements.append(Spacer(1, 5 * mm))

    coaching = _safe_get(analysis_result, "coaching", {})
    details = _safe_get(coaching, "details", [])

    if not details:
        elements.append(Paragraph("コーチングデータがありません。", styles["body"]))
        return elements

    priority_labels = {
        "high": "高",
        "medium": "中",
        "low": "低",
    }

    for detail in details:
        joint = _safe_get(detail, "joint", "")
        advice = _safe_get(detail, "advice", "")
        priority_raw = _safe_get(detail, "priority", "")
        priority = priority_labels.get(priority_raw, priority_raw)

        elements.append(
            Paragraph(
                f"【優先度: {xml_escape(priority)}】 {xml_escape(joint)}",
                styles["subheading"],
            ),
        )
        elements.append(Paragraph(xml_escape(advice), styles["body"]))
        elements.append(Spacer(1, 3 * mm))

    return elements


class ReportGenerator:
    """解析結果をPDFレポートとして出力する.

    セクション構成:
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
        logger.info("Generating PDF report: %s", output_path)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
        )

        styles = _build_styles()

        elements: list = []
        elements.extend(_build_cover_page(analysis_result, styles))
        elements.extend(_build_score_page(analysis_result, styles))
        elements.extend(_build_angle_summary_page(analysis_result, styles))
        elements.extend(_build_graph_page(analysis_result, styles))
        elements.extend(_build_comparison_page(analysis_result, styles))
        elements.extend(_build_coaching_page(analysis_result, styles))

        doc.build(elements)
        logger.info(
            "PDF report generated: %s (%d bytes)",
            output_path,
            output_path.stat().st_size,
        )

        return output_path
