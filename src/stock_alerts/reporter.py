from __future__ import annotations

from stock_alerts.models import StockReport, TechnicalSignal


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
        "🎯 เป้าหมาย: คัดหุ้นที่น่าศึกษาต่อ ไม่ใช่คำสั่งซื้อขาย",
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
        f"#{index} 📌 {report.profile.ticker} - {report.profile.name}",
        f"🏢 {report.profile.business}",
        f"🧠 {signal.stance} | score {signal.score}",
        f"💰 {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
        f"📊 {_format_indicators(signal)}",
        "✅ เหตุผล:",
        *[f"• {reason}" for reason in signal.reasons],
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
            f"📰 ข่าวนำ: {lead_news.title}",
            f"🧾 สรุปข่าว: {_format_news_summary(lead_news.summary)}",
            f"🔗 {lead_news.link}",
        ]
    )


def _format_news_summary(summary: str | None) -> str:
    if not summary:
        return "feed ไม่มีสรุปข่าว ให้ตรวจรายละเอียดจากลิงก์"
    return summary


def _format_indicators(signal: TechnicalSignal) -> str:
    rsi = _format_optional(signal.rsi)
    sma_20 = _format_optional(signal.sma_20)
    sma_50 = _format_optional(signal.sma_50)
    macd = _format_optional(signal.macd)
    macd_signal = _format_optional(signal.macd_signal)
    return f"RSI: {rsi} | SMA20: {sma_20} | SMA50: {sma_50} | MACD: {macd}/{macd_signal}"


def _format_optional(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f}"
