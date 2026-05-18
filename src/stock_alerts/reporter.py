from __future__ import annotations

from stock_alerts.models import StockReport, TechnicalSignal
from stock_alerts.sop import assess_report_with_sop, calculate_opportunity_score, strongest_news_score_for

MAX_DIGEST_NEWS_TITLE_LENGTH = 160
MAX_DIGEST_NEWS_SUMMARY_LENGTH = 180
MAX_DIGEST_TEXT_LENGTH = 140
MAX_DIGEST_REASONS = 3
MAX_DIGEST_RISK_FLAGS = 2


def build_digest_message(
    reports: list[StockReport],
    scanned_count: int,
    matched_count: int,
    message_index: int = 1,
    message_count: int = 1,
    rank_start: int = 1,
) -> str:
    lines = [
        "📈 Stock Opportunity Digest",
        f"🧭 ชุดที่ {message_index}/{message_count}",
        f"🔎 สแกน {scanned_count} ตัว | เข้าเกณฑ์ {matched_count} ตัว | ชุดนี้ {len(reports)} ตัว",
        "🎯 เป้าหมาย: คัด high-conviction candidate จากกราฟ+ข่าว ไม่ใช่คำสั่งซื้อขาย",
        "",
    ]

    for index, report in enumerate(reports, start=rank_start):
        lines.extend(_format_digest_report(index, report))

    lines.extend(
        [
            "⚠️ หมายเหตุ",
            "ตัวที่ score สูงคือ candidate สำหรับศึกษาต่อ ไม่ใช่การการันตีว่าจะขึ้นหรือกำไร 100-200%",
            "ก่อนลงทุนควรตรวจงบ, valuation, catalyst, สภาพคล่อง, จุดตัดขาดทุน และขนาด position",
        ]
    )
    return "\n".join(lines)


def build_report_message(report: StockReport) -> str:
    signal = report.signal
    lines = [
        f"📌 {report.profile.ticker} - {report.profile.name}",
        f"🏢 ธุรกิจ: {report.profile.business}",
        f"🧠 มุมมองระบบ: {signal.stance} (score {signal.score})",
        f"💰 ราคาล่าสุด: {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
        "📊 " + _format_indicators(signal),
        "",
        "✅ เหตุผล:",
        *[f"• {reason}" for reason in signal.reasons],
    ]

    if report.news:
        lines.extend(["", "📰 ข่าวล่าสุด:"])
        for item in report.news:
            lines.extend(
                [
                    f"• {item.title}",
                    f"  🧾 สรุป: {_format_news_summary(item.summary)}",
                    f"  🔗 {item.link}",
                ]
            )
    else:
        lines.extend(["", "📰 ข่าวล่าสุด: ยังไม่พบข่าวจาก feed ที่ใช้"])

    lines.extend(
        [
            "",
            "⚠️ หมายเหตุ: เป็นสัญญาณช่วยคัดกรอง ไม่ใช่คำแนะนำการลงทุน",
        ]
    )
    return "\n".join(lines)


def _format_digest_report(index: int, report: StockReport) -> list[str]:
    signal = report.signal
    sop_assessment = assess_report_with_sop(report)
    lines = [
        "━━━━━━━━━━━━━━",
        f"#{index} 📌 {report.profile.ticker} - {_shorten(report.profile.name, MAX_DIGEST_TEXT_LENGTH)}",
        f"🏢 ทำอะไร: {_shorten(report.profile.business, MAX_DIGEST_TEXT_LENGTH)}",
        f"🧩 จำเป็นต่อ: {sop_assessment.business_importance}",
        f"🧠 {signal.stance} | technical {signal.score} | opportunity {_calculate_opportunity_score(report)}",
        f"🔮 โอกาสขึ้น: {sop_assessment.upside_view}",
        f"🧭 SOP next step: {sop_assessment.decision_note}",
        f"🏷️ {_format_tags(report)}",
        f"📈 Trend: {signal.trend}",
        f"💰 {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
        f"📊 {_format_indicators(signal)}",
        f"🧮 {_format_advanced_indicators(signal)}",
        *_format_technical_plan(signal),
        "✅ เหตุผล:",
        *[f"• {_shorten(reason, MAX_DIGEST_TEXT_LENGTH)}" for reason in signal.reasons[:MAX_DIGEST_REASONS]],
        *_format_risk_flags(signal),
        _format_lead_news(report),
        "",
    ]
    return lines


def _format_lead_news(report: StockReport) -> str:
    if not report.news:
        return "📰 ข่าวนำ: ยังไม่พบข่าวจาก feed ที่ใช้"

    lead_news = report.news[0]
    sop_assessment = assess_report_with_sop(report)
    return "\n".join(
        [
            f"📰 ข่าวนำ: {_shorten(lead_news.title, MAX_DIGEST_NEWS_TITLE_LENGTH)}",
            f"🕒 เวลา: {_format_published_at(lead_news.published)}",
            f"🧾 สรุปข่าว: {_shorten(_format_news_summary(lead_news.summary), MAX_DIGEST_NEWS_SUMMARY_LENGTH)}",
            f"🗞️ Tone: {_format_sentiment(lead_news.sentiment, lead_news.sentiment_score)}",
            f"🧠 วิเคราะห์ข่าว: {sop_assessment.news_impact}",
            f"🔗 {lead_news.link}",
        ]
    )


def _format_news_summary(summary: str | None) -> str:
    if not summary:
        return "feed ไม่มีสรุปข่าว ให้ตรวจรายละเอียดจากลิงก์"
    return summary


def _format_published_at(published: str | None) -> str:
    if not published:
        return "ไม่ระบุ"
    return published


def _format_indicators(signal: TechnicalSignal) -> str:
    rsi = _format_optional(signal.rsi)
    sma_20 = _format_optional(signal.sma_20)
    sma_50 = _format_optional(signal.sma_50)
    macd = _format_optional(signal.macd)
    macd_signal = _format_optional(signal.macd_signal)
    adx = _format_optional(signal.adx)
    atr_percent = _format_percent(signal.atr_percent)
    high_distance = _format_percent(signal.distance_from_high_percent)
    return (
        f"RSI: {rsi} | SMA20: {sma_20} | SMA50: {sma_50} | MACD: {macd}/{macd_signal} | "
        f"ADX: {adx} | ATR: {atr_percent} | 60D high: {high_distance}"
    )


def _format_advanced_indicators(signal: TechnicalSignal) -> str:
    rsi_fast = _format_optional(signal.rsi_fast)
    rsi_default = _format_optional(signal.rsi)
    rsi_slow = _format_optional(signal.rsi_slow)
    plus_di = _format_optional(signal.plus_di)
    minus_di = _format_optional(signal.minus_di)
    stop = _format_optional(signal.atr_stop_loss)
    target_2x = _format_optional(signal.atr_take_profit_2x)
    target_3x = _format_optional(signal.atr_take_profit_3x)
    return (
        f"RSI5/14/21: {rsi_fast}/{rsi_default}/{rsi_slow} | "
        f"+DI/-DI: {plus_di}/{minus_di} | ATR stop/TP: {stop}/{target_2x}/{target_3x}"
    )


def _format_technical_plan(signal: TechnicalSignal) -> list[str]:
    if not signal.technical_plan:
        return []
    return ["🗺️ Technical plan:", *[f"• {_shorten(item, MAX_DIGEST_TEXT_LENGTH)}" for item in signal.technical_plan]]


def _format_risk_flags(signal: TechnicalSignal) -> list[str]:
    if not signal.risk_flags:
        return []
    return [
        "⚠️ จุดที่ต้องระวัง:",
        *[f"• {_shorten(risk_flag, MAX_DIGEST_TEXT_LENGTH)}" for risk_flag in signal.risk_flags[:MAX_DIGEST_RISK_FLAGS]],
    ]


def _format_sentiment(sentiment: str, score: int) -> str:
    labels = {
        "positive": "บวก",
        "slightly_positive": "เริ่มบวก",
        "neutral": "กลาง",
        "slightly_negative": "เริ่มลบ",
        "negative": "ลบ",
    }
    return f"{labels.get(sentiment, sentiment)} ({score:+d})"


def _format_tags(report: StockReport) -> str:
    tags: list[str] = []
    opportunity_score = _calculate_opportunity_score(report)
    strongest_news_score = _strongest_news_score(report)

    if opportunity_score >= 7:
        tags.append("🚀 น่าสนใจมาก")
    elif opportunity_score >= 4:
        tags.append("👀 น่าจับตา")

    if strongest_news_score >= 2:
        tags.append("🔥 ข่าวบวกแรง")
    elif strongest_news_score <= -2:
        tags.append("⚠️ ข่าวลบแรง")

    if report.signal.trend == "ขาขึ้นแข็งแรง":
        tags.append("📈 trend แข็งแรง")
    if report.signal.risk_flags:
        tags.append("🛡️ เช็กความเสี่ยง")

    return " | ".join(tags) if tags else "รอติดตามต่อ"


def _calculate_opportunity_score(report: StockReport) -> int:
    return calculate_opportunity_score(report)


def _strongest_news_score(report: StockReport) -> int:
    return strongest_news_score_for(report)


def _format_optional(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:+.2f}%"


def _shorten(value: str, max_length: int) -> str:
    normalized_value = " ".join(value.split())
    if len(normalized_value) <= max_length:
        return normalized_value
    return normalized_value[: max_length - 1].rstrip() + "…"
