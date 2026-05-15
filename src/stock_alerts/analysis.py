from __future__ import annotations

import pandas as pd

from stock_alerts.models import TechnicalSignal


RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 35
MIN_HISTORY_ROWS = 60


def analyze_technical_signal(ticker: str, history: pd.DataFrame) -> TechnicalSignal:
    if len(history.index) < MIN_HISTORY_ROWS:
        raise ValueError(f"Need at least {MIN_HISTORY_ROWS} rows of history for {ticker}")

    frame = history.copy()
    frame["sma_20"] = frame["Close"].rolling(window=20).mean()
    frame["sma_50"] = frame["Close"].rolling(window=50).mean()
    frame["rsi"] = _calculate_rsi(frame["Close"])
    frame["macd"], frame["macd_signal"] = _calculate_macd(frame["Close"])
    frame["avg_volume_20"] = frame["Volume"].rolling(window=20).mean()
    frame["high_20"] = frame["Close"].rolling(window=20).max()

    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    close_price = float(latest["Close"])
    previous_close = float(previous["Close"])
    change_percent = ((close_price - previous_close) / previous_close) * 100

    score = 0
    reasons: list[str] = []

    if _is_above(latest, "Close", "sma_20") and _is_above(latest, "sma_20", "sma_50"):
        score += 2
        reasons.append("ราคาอยู่เหนือ SMA20 และ SMA20 อยู่เหนือ SMA50")

    if _crossed_up(previous, latest, "macd", "macd_signal"):
        score += 2
        reasons.append("MACD ตัดขึ้นเหนือ signal line")

    latest_rsi = _read_optional_float(latest, "rsi")
    if latest_rsi is not None:
        if RSI_OVERSOLD <= latest_rsi <= RSI_OVERBOUGHT:
            score += 1
            reasons.append("RSI อยู่ในโซนที่ยังไม่ร้อนแรงเกินไป")
        elif latest_rsi > RSI_OVERBOUGHT:
            score -= 2
            reasons.append("RSI สูงกว่า 70 เสี่ยง overbought")

    if _is_volume_breakout(latest):
        score += 1
        reasons.append("Volume ล่าสุดสูงกว่าค่าเฉลี่ย 20 วัน")

    if _is_price_breakout(previous, latest):
        score += 1
        reasons.append("ราคาทำ breakout เทียบกรอบ 20 วัน")

    stance = _build_stance(score)
    if not reasons:
        reasons.append("ยังไม่มีสัญญาณเด่นพอ ต้องติดตามต่อ")

    return TechnicalSignal(
        ticker=ticker,
        score=score,
        stance=stance,
        close_price=close_price,
        change_percent=change_percent,
        rsi=latest_rsi,
        sma_20=_read_optional_float(latest, "sma_20"),
        sma_50=_read_optional_float(latest, "sma_50"),
        macd=_read_optional_float(latest, "macd"),
        macd_signal=_read_optional_float(latest, "macd_signal"),
        reasons=tuple(reasons),
    )


def _calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=window).mean()
    loss = (-delta.clip(upper=0)).rolling(window=window).mean()
    relative_strength = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + relative_strength))


def _calculate_macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def _is_above(row: pd.Series, left_key: str, right_key: str) -> bool:
    left = _read_optional_float(row, left_key)
    right = _read_optional_float(row, right_key)
    return left is not None and right is not None and left > right


def _crossed_up(previous: pd.Series, latest: pd.Series, left_key: str, right_key: str) -> bool:
    previous_left = _read_optional_float(previous, left_key)
    previous_right = _read_optional_float(previous, right_key)
    latest_left = _read_optional_float(latest, left_key)
    latest_right = _read_optional_float(latest, right_key)
    if None in {previous_left, previous_right, latest_left, latest_right}:
        return False
    return previous_left <= previous_right and latest_left > latest_right


def _is_volume_breakout(latest: pd.Series) -> bool:
    volume = _read_optional_float(latest, "Volume")
    average_volume = _read_optional_float(latest, "avg_volume_20")
    return volume is not None and average_volume is not None and volume > average_volume * 1.5


def _is_price_breakout(previous: pd.Series, latest: pd.Series) -> bool:
    previous_high = _read_optional_float(previous, "high_20")
    latest_close = _read_optional_float(latest, "Close")
    return previous_high is not None and latest_close is not None and latest_close > previous_high


def _read_optional_float(row: pd.Series, key: str) -> float | None:
    value = row.get(key)
    if pd.isna(value):
        return None
    return float(value)


def _build_stance(score: int) -> str:
    if score >= 4:
        return "น่าจับตามองมาก"
    if score >= 2:
        return "น่าติดตาม"
    if score <= -1:
        return "ควรระวัง"
    return "ยังไม่เด่น"
