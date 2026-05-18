from __future__ import annotations

from stock_alerts.models import StockReport, TechnicalSignal

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
) -> str:
    lines = [
        "📈 Stock Opportunity Digest",
        f"🧭 ชุดที่ {message_index}/{message_count}",
        f"🔎 สแกน {scanned_count} ตัว | เข้าเกณฑ์ {matched_count} ตัว | ชุดนี้ {len(reports)} ตัว",
        "🎯 เป้าหมาย: คัด high-conviction candidate จากกราฟ+ข่าว ไม่ใช่คำสั่งซื้อขาย",
        "",
    ]

    for index, report in enumerate(reports, start=1):
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
    lines = [
        "━━━━━━━━━━━━━━",
        f"#{index} 📌 {report.profile.ticker} - {_shorten(report.profile.name, MAX_DIGEST_TEXT_LENGTH)}",
        f"🏢 ทำอะไร: {_shorten(report.profile.business, MAX_DIGEST_TEXT_LENGTH)}",
        f"🧩 จำเป็นต่อ: {_format_business_importance(report)}",
        f"🧠 {signal.stance} | technical {signal.score} | opportunity {_calculate_opportunity_score(report)}",
        f"🔮 โอกาสขึ้น: {_format_upside_view(report)}",
        f"🏷️ {_format_tags(report)}",
        f"📈 Trend: {signal.trend}",
        f"💰 {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
        f"📊 {_format_indicators(signal)}",
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
    return "\n".join(
        [
            f"📰 ข่าวนำ: {_shorten(lead_news.title, MAX_DIGEST_NEWS_TITLE_LENGTH)}",
            f"🕒 เวลา: {_format_published_at(lead_news.published)}",
            f"🧾 สรุปข่าว: {_shorten(_format_news_summary(lead_news.summary), MAX_DIGEST_NEWS_SUMMARY_LENGTH)}",
            f"🗞️ Tone: {_format_sentiment(lead_news.sentiment, lead_news.sentiment_score)}",
            f"🧠 วิเคราะห์ข่าว: {_format_news_impact(report)}",
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


def _format_upside_view(report: StockReport) -> str:
    opportunity_score = _calculate_opportunity_score(report)
    signal = report.signal

    if opportunity_score >= 8 and signal.trend == "ขาขึ้นแข็งแรง" and not signal.risk_flags:
        return "สูงมากถ้าข่าว/volume หนุนต่อ แต่ต้องรอจังหวะและจุดตัดขาดทุน"
    if opportunity_score >= 7:
        return "สูง เหมาะติดตาม breakout/ข่าวต่อเนื่อง"
    if opportunity_score >= 5:
        return "ปานกลางถึงสูง ต้องยืนยันด้วยข่าวและแรงซื้อรอบถัดไป"
    if opportunity_score >= 3:
        return "เริ่มน่าสนใจ แต่ยังต้องรอสัญญาณยืนยัน"
    return "ยังไม่เด่นพอ เน้นเฝ้าดูมากกว่าตัดสินใจทันที"


def _format_news_impact(report: StockReport) -> str:
    strongest_news_score = _strongest_news_score(report)
    if not report.news:
        return "ยังไม่มีข่าวให้ยืนยัน ต้องพึ่งกราฟเป็นหลัก"
    if strongest_news_score >= 3:
        return "ข่าวบวกแรง อาจเป็น catalyst เพิ่มแรงซื้อถ้าตลาดตอบรับต่อ"
    if strongest_news_score >= 1:
        return "ข่าวเอนบวก ช่วยหนุน sentiment แต่ยังควรดู volume/ราคา follow-through"
    if strongest_news_score <= -3:
        return "ข่าวลบแรง อาจกด upside หรือทำให้ผันผวนสูง"
    if strongest_news_score <= -1:
        return "ข่าวเอนลบ ต้องระวังแรงขายหรือ sentiment แผ่ว"
    return "ข่าวกลาง ๆ ยังไม่ใช่ catalyst หลัก"


def _format_business_importance(report: StockReport) -> str:
    text = f"{report.profile.business} {report.profile.sector or ''} {report.profile.industry or ''}".lower()
    if any(keyword in text for keyword in ("semiconductor", "ai", "artificial intelligence", "chip")):
        return "โครงสร้างพื้นฐาน AI/data center และ supply chain ชิป"
    if any(keyword in text for keyword in ("software", "cloud", "cybersecurity")):
        return "ระบบดิจิทัลขององค์กร, cloud, data และ productivity"
    if any(keyword in text for keyword in ("bank", "finance", "payment", "insurance", "asset management")):
        return "ระบบการเงิน, credit, payment และการหมุนเวียนเงินในเศรษฐกิจ"
    if any(keyword in text for keyword in ("aerospace", "defense", "machinery", "industrial", "logistics", "transportation", "trucking")):
        return "โครงสร้างเศรษฐกิจจริง เช่น การผลิต, ขนส่ง, logistics และความมั่นคง"
    if any(keyword in text for keyword in ("health", "medical", "biotechnology", "drug")):
        return "บริการสุขภาพ ยา และโครงสร้างพื้นฐานทางการแพทย์"
    if any(keyword in text for keyword in ("media", "advertising", "internet", "retail", "travel", "consumer")):
        return "พฤติกรรมผู้บริโภค, แพลตฟอร์มออนไลน์, โฆษณา และบริการรายวัน"
    if any(keyword in text for keyword in ("telecommunication", "communication")):
        return "โครงข่ายสื่อสารและ connectivity สำหรับผู้ใช้/องค์กร"
    return "ธุรกิจในห่วงโซ่เศรษฐกิจของกลุ่มที่คัดไว้ ควรอ่านรายละเอียดเพิ่มก่อนตัดสินใจ"


def _calculate_opportunity_score(report: StockReport) -> int:
    return report.signal.score + _strongest_news_score(report)


def _strongest_news_score(report: StockReport) -> int:
    return max((news_item.sentiment_score for news_item in report.news), default=0)


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
