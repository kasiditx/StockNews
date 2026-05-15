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
        "Stock Opportunity Digest",
        f"ชุดที่: {message_index}/{message_count}",
        f"สแกนทั้งหมด: {scanned_count} ตัว | เข้าเกณฑ์: {matched_count} ตัว | แสดงชุดนี้: {len(reports)} ตัว",
        "เป้าหมาย: คัดตัวที่น่าศึกษาต่อ ไม่ใช่คำสั่งซื้อขาย",
        "",
    ]

    for index, report in enumerate(reports, start=1):
        signal = report.signal
        lines.extend(
            [
                f"{index}. {report.profile.ticker} - {report.profile.name}",
                f"ธุรกิจ: {report.profile.business}",
                f"มุมมอง: {signal.stance} (score {signal.score})",
                f"ราคา: {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
                _format_indicators(signal),
                "เหตุผล: " + "; ".join(signal.reasons),
            ]
        )

        if report.news:
            lead_news = report.news[0]
            lines.append(f"ข่าวนำ: {lead_news.title}: {lead_news.link}")
        else:
            lines.append("ข่าวนำ: ยังไม่พบข่าวจาก feed ที่ใช้")
        lines.append("")

    lines.extend(
        [
            "อ่านแบบมืออาชีพ: ตัวที่ score สูงคือ candidate สำหรับศึกษาต่อ "
            "ไม่ใช่การการันตีว่าจะขึ้นหรือกำไร 100-200%",
            "ต้องตรวจงบ, valuation, catalyst, สภาพคล่อง, จุดตัดขาดทุน และขนาด position ก่อนลงทุน",
        ]
    )
    return "\n".join(lines)


def build_report_message(report: StockReport) -> str:
    signal = report.signal
    lines = [
        f"{report.profile.ticker} - {report.profile.name}",
        f"ธุรกิจ: {report.profile.business}",
        f"มุมมองระบบ: {signal.stance} (score {signal.score})",
        f"ราคาล่าสุด: {signal.close_price:,.2f} ({signal.change_percent:+.2f}%)",
        _format_indicators(signal),
        "",
        "เหตุผล:",
        *[f"- {reason}" for reason in signal.reasons],
    ]

    if report.news:
        lines.extend(["", "ข่าวล่าสุด:"])
        lines.extend(f"- {item.title}: {item.link}" for item in report.news)
    else:
        lines.extend(["", "ข่าวล่าสุด: ยังไม่พบข่าวจาก feed ที่ใช้"])

    lines.extend(
        [
            "",
            "หมายเหตุ: เป็นสัญญาณช่วยคัดกรอง ไม่ใช่คำแนะนำการลงทุน",
        ]
    )
    return "\n".join(lines)


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
