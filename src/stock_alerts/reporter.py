from __future__ import annotations

from stock_alerts.models import StockReport, TechnicalSignal


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
