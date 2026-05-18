from __future__ import annotations

import pandas as pd

from stock_alerts.models import TechnicalSignal


RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 35
MIN_HISTORY_ROWS = 60
ADX_STRONG_TREND = 25
ATR_HIGH_VOLATILITY_PERCENT = 6
BOLLINGER_UPPER_ZONE = 0.9
BOLLINGER_LOWER_ZONE = 0.1
RSI_FAST_WINDOW = 5
RSI_DEFAULT_WINDOW = 14
RSI_SLOW_WINDOW = 21
SMA20_EXTENDED_DISTANCE_PERCENT = 8
ATR_STOP_MULTIPLIER = 1.5
ATR_TARGET_2X_MULTIPLIER = 2
ATR_TARGET_3X_MULTIPLIER = 3


def analyze_technical_signal(ticker: str, history: pd.DataFrame) -> TechnicalSignal:
    if len(history.index) < MIN_HISTORY_ROWS:
        raise ValueError(f"Need at least {MIN_HISTORY_ROWS} rows of history for {ticker}")

    frame = history.copy()
    frame["sma_20"] = frame["Close"].rolling(window=20).mean()
    frame["sma_50"] = frame["Close"].rolling(window=50).mean()
    frame["rsi_fast"] = _calculate_rsi(frame["Close"], window=RSI_FAST_WINDOW)
    frame["rsi"] = _calculate_rsi(frame["Close"], window=RSI_DEFAULT_WINDOW)
    frame["rsi_slow"] = _calculate_rsi(frame["Close"], window=RSI_SLOW_WINDOW)
    frame["macd"], frame["macd_signal"] = _calculate_macd(frame["Close"])
    frame["adx"], frame["plus_di"], frame["minus_di"] = _calculate_adx(frame)
    frame["atr"] = _calculate_atr(frame)
    frame["atr_percent"] = frame["atr"] / frame["Close"] * 100
    frame["bb_position"] = _calculate_bollinger_position(frame["Close"])
    frame["avg_volume_20"] = frame["Volume"].rolling(window=20).mean()
    frame["high_20"] = frame["Close"].rolling(window=20).max()
    frame["high_60"] = frame["Close"].rolling(window=60).max()

    latest = frame.iloc[-1]
    previous = frame.iloc[-2]
    close_price = float(latest["Close"])
    previous_close = float(previous["Close"])
    change_percent = ((close_price - previous_close) / previous_close) * 100

    score = 0
    reasons: list[str] = []
    risk_flags: list[str] = []
    technical_plan: list[str] = []

    if _is_above(latest, "Close", "sma_20") and _is_above(latest, "sma_20", "sma_50"):
        score += 2
        reasons.append("trend หลักเป็นขาขึ้น: ราคาอยู่เหนือ SMA20 และ SMA20 อยู่เหนือ SMA50")
        technical_plan.append("SMA setup: trend ขาขึ้นระยะสั้น ใช้ SMA20 เป็นแนวรับ dynamic")

    if _crossed_up(previous, latest, "Close", "sma_20"):
        score += 1
        reasons.append("ราคาปิดทะลุ SMA20 ขึ้นมา เป็นสัญญาณเริ่มกลับมาแข็งแรง")
    elif _crossed_down(previous, latest, "Close", "sma_20"):
        score -= 1
        risk_flags.append("ราคาปิดหลุด SMA20 ลงมา ต้องระวัง momentum แผ่ว")

    latest_adx = _read_optional_float(latest, "adx")
    latest_plus_di = _read_optional_float(latest, "plus_di")
    latest_minus_di = _read_optional_float(latest, "minus_di")
    if latest_adx is not None:
        if latest_adx >= ADX_STRONG_TREND and _is_above(latest, "plus_di", "minus_di"):
            score += 2
            reasons.append(f"ADX {latest_adx:.1f} และ +DI เหนือ -DI บอกว่า trend ขาขึ้นแข็งแรง")
            technical_plan.append("ADX/+DI: trend มีแรงฝั่งขึ้น ใช้ pullback หรือ breakout เป็นจุดติดตาม")
        elif latest_adx >= ADX_STRONG_TREND and _is_above(latest, "minus_di", "plus_di"):
            score -= 2
            risk_flags.append(f"ADX {latest_adx:.1f} แต่ -DI เหนือ +DI แปลว่า trend ขาลงแข็งแรง")
        elif latest_adx < 18:
            risk_flags.append(f"ADX {latest_adx:.1f} ยังบอกว่า trend ไม่ชัด")

    if _crossed_up(previous, latest, "macd", "macd_signal"):
        score += 2
        if _is_below(latest, "macd", "zero_line"):
            reasons.append("MACD ตัดขึ้นใต้เส้น 0: มีโอกาสเป็นต้นเทรนด์ แต่ต้องรอ follow-through")
        else:
            reasons.append("MACD ตัดขึ้นเหนือ signal line")
        technical_plan.append("MACD: รอดูการยืนเหนือ signal ต่อเนื่องเพื่อยืนยัน momentum")
    elif _crossed_down(previous, latest, "macd", "macd_signal"):
        risk_flags.append("MACD ตัดลงใต้ signal line ระวัง momentum อ่อนตัว")

    latest_rsi = _read_optional_float(latest, "rsi")
    latest_rsi_fast = _read_optional_float(latest, "rsi_fast")
    latest_rsi_slow = _read_optional_float(latest, "rsi_slow")
    if latest_rsi is not None:
        if RSI_OVERSOLD <= latest_rsi <= RSI_OVERBOUGHT:
            score += 1
            reasons.append("RSI อยู่ในโซนที่ยังไม่ร้อนแรงเกินไป")
        elif latest_rsi > RSI_OVERBOUGHT:
            score -= 2
            risk_flags.append("RSI สูงกว่า 70 เสี่ยง overbought")
        elif latest_rsi < RSI_OVERSOLD:
            risk_flags.append("RSI ต่ำกว่า 35 ยังอ่อนแรง ต้องรอสัญญาณกลับตัว")

    if _crossed_up(previous, latest, "rsi_fast", "rsi"):
        score += 1
        reasons.append("RSI5 ตัดขึ้นเหนือ RSI14 เป็นสัญญาณ momentum ระยะสั้นเริ่มดีขึ้น")
    elif _crossed_down(previous, latest, "rsi_fast", "rsi"):
        risk_flags.append("RSI5 ตัดลงใต้ RSI14 ระวัง momentum ระยะสั้นอ่อนลง")

    if latest_rsi_slow is not None and latest_rsi is not None and latest_rsi > latest_rsi_slow:
        technical_plan.append("RSI multi-period: RSI14 อยู่เหนือ RSI21 หนุนภาพ swing/trend")

    if _is_volume_breakout(latest):
        score += 1
        reasons.append("Volume ล่าสุดสูงกว่าค่าเฉลี่ย 20 วัน")

    if _is_price_breakout(previous, latest):
        score += 1
        reasons.append("ราคาทำ breakout เทียบกรอบ 20 วัน")

    if _is_sixty_day_breakout(previous, latest):
        score += 2
        reasons.append("ราคาทำ breakout เหนือกรอบ 60 วัน")

    latest_bb_position = _read_optional_float(latest, "bb_position")
    if latest_bb_position is not None:
        if latest_bb_position >= BOLLINGER_UPPER_ZONE:
            score += 1
            reasons.append("ราคาอยู่โซนบนของ Bollinger Band สะท้อน momentum")
        elif latest_bb_position <= BOLLINGER_LOWER_ZONE:
            risk_flags.append("ราคาอยู่โซนล่างของ Bollinger Band ต้องระวังแรงขาย")

    latest_atr_percent = _read_optional_float(latest, "atr_percent")
    latest_atr = _read_optional_float(latest, "atr")
    if latest_atr_percent is not None and latest_atr_percent >= ATR_HIGH_VOLATILITY_PERCENT:
        risk_flags.append(f"ATR {latest_atr_percent:.1f}% ผันผวนสูง ควรลดขนาด position")
    if latest_atr is not None:
        technical_plan.append(
            "ATR plan: stop ประมาณ "
            f"{_format_price(close_price - (latest_atr * ATR_STOP_MULTIPLIER))}, "
            f"target 2ATR {_format_price(close_price + (latest_atr * ATR_TARGET_2X_MULTIPLIER))}, "
            f"target 3ATR {_format_price(close_price + (latest_atr * ATR_TARGET_3X_MULTIPLIER))}"
        )

    sma_20_distance = _calculate_distance_between(latest, "Close", "sma_20")
    if sma_20_distance is not None and sma_20_distance >= SMA20_EXTENDED_DISTANCE_PERCENT:
        risk_flags.append(f"ราคาห่าง SMA20 {sma_20_distance:.1f}% เสี่ยงไล่ราคา ควรรอ pullback")
    elif sma_20_distance is not None and 0 <= sma_20_distance <= 3:
        technical_plan.append("SMA20 pullback: ราคาใกล้ SMA20 เหมาะดูแท่งกลับตัว/volume เพื่อหา entry")

    stance = _build_stance(score)
    if not reasons:
        reasons.append("ยังไม่มีสัญญาณเด่นพอ ต้องติดตามต่อ")
    trend = _build_trend_label(latest, score)

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
        adx=latest_adx,
        atr_percent=latest_atr_percent,
        bollinger_position=latest_bb_position,
        distance_from_high_percent=_calculate_distance_from_high(latest),
        trend=trend,
        reasons=tuple(reasons),
        risk_flags=tuple(risk_flags),
        rsi_fast=latest_rsi_fast,
        rsi_slow=latest_rsi_slow,
        plus_di=latest_plus_di,
        minus_di=latest_minus_di,
        atr_stop_loss=_calculate_atr_level(close_price, latest_atr, -ATR_STOP_MULTIPLIER),
        atr_take_profit_2x=_calculate_atr_level(close_price, latest_atr, ATR_TARGET_2X_MULTIPLIER),
        atr_take_profit_3x=_calculate_atr_level(close_price, latest_atr, ATR_TARGET_3X_MULTIPLIER),
        technical_plan=tuple(technical_plan[:4]),
    )


def _calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=window).mean()
    loss = (-delta.clip(upper=0)).rolling(window=window).mean()
    relative_strength = gain / loss.where(loss != 0)
    rsi = 100 - (100 / (1 + relative_strength))
    return rsi.mask((loss == 0) & (gain > 0), 100)


def _calculate_macd(close: pd.Series) -> tuple[pd.Series, pd.Series]:
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def _calculate_adx(frame: pd.DataFrame, window: int = 14) -> tuple[pd.Series, pd.Series, pd.Series]:
    high = frame["High"]
    low = frame["Low"]

    plus_dm = (high.diff()).where((high.diff() > -low.diff()) & (high.diff() > 0), 0)
    minus_dm = (-low.diff()).where((-low.diff() > high.diff()) & (-low.diff() > 0), 0)
    atr = _calculate_atr(frame, window=window)
    plus_di = 100 * plus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / window, adjust=False).mean() / atr
    directional_index_denominator = plus_di + minus_di
    dx = ((plus_di - minus_di).abs() / directional_index_denominator.where(
        directional_index_denominator != 0
    )) * 100
    adx = dx.ewm(alpha=1 / window, adjust=False).mean()
    return adx, plus_di, minus_di


def _calculate_atr(frame: pd.DataFrame, window: int = 14) -> pd.Series:
    high_low = frame["High"] - frame["Low"]
    high_close = (frame["High"] - frame["Close"].shift()).abs()
    low_close = (frame["Low"] - frame["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.ewm(alpha=1 / window, adjust=False).mean()


def _calculate_bollinger_position(close: pd.Series, window: int = 20) -> pd.Series:
    middle_band = close.rolling(window=window).mean()
    standard_deviation = close.rolling(window=window).std()
    upper_band = middle_band + (standard_deviation * 2)
    lower_band = middle_band - (standard_deviation * 2)
    band_width = (upper_band - lower_band).replace(0, pd.NA)
    return (close - lower_band) / band_width


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


def _crossed_down(previous: pd.Series, latest: pd.Series, left_key: str, right_key: str) -> bool:
    previous_left = _read_optional_float(previous, left_key)
    previous_right = _read_optional_float(previous, right_key)
    latest_left = _read_optional_float(latest, left_key)
    latest_right = _read_optional_float(latest, right_key)
    if None in {previous_left, previous_right, latest_left, latest_right}:
        return False
    return previous_left >= previous_right and latest_left < latest_right


def _is_below(row: pd.Series, left_key: str, right_key: str) -> bool:
    left = _read_optional_float(row, left_key)
    right = _read_optional_float(row, right_key)
    return left is not None and right is not None and left < right


def _is_volume_breakout(latest: pd.Series) -> bool:
    volume = _read_optional_float(latest, "Volume")
    average_volume = _read_optional_float(latest, "avg_volume_20")
    return volume is not None and average_volume is not None and volume > average_volume * 1.5


def _is_price_breakout(previous: pd.Series, latest: pd.Series) -> bool:
    previous_high = _read_optional_float(previous, "high_20")
    latest_close = _read_optional_float(latest, "Close")
    return previous_high is not None and latest_close is not None and latest_close > previous_high


def _is_sixty_day_breakout(previous: pd.Series, latest: pd.Series) -> bool:
    previous_high = _read_optional_float(previous, "high_60")
    latest_close = _read_optional_float(latest, "Close")
    return previous_high is not None and latest_close is not None and latest_close > previous_high


def _calculate_distance_from_high(row: pd.Series) -> float | None:
    latest_close = _read_optional_float(row, "Close")
    high_60 = _read_optional_float(row, "high_60")
    if latest_close is None or high_60 is None or high_60 == 0:
        return None
    return ((latest_close - high_60) / high_60) * 100


def _calculate_distance_between(row: pd.Series, left_key: str, right_key: str) -> float | None:
    left = _read_optional_float(row, left_key)
    right = _read_optional_float(row, right_key)
    if left is None or right is None or right == 0:
        return None
    return ((left - right) / right) * 100


def _calculate_atr_level(close_price: float, atr: float | None, multiplier: float) -> float | None:
    if atr is None:
        return None
    return close_price + (atr * multiplier)


def _format_price(value: float) -> str:
    return f"{value:,.2f}"


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


def _build_trend_label(latest: pd.Series, score: int) -> str:
    adx = _read_optional_float(latest, "adx")
    close_above_sma_20 = _is_above(latest, "Close", "sma_20")
    sma_20_above_sma_50 = _is_above(latest, "sma_20", "sma_50")

    plus_di_above_minus_di = _is_above(latest, "plus_di", "minus_di")

    if (
        close_above_sma_20
        and sma_20_above_sma_50
        and adx is not None
        and adx >= ADX_STRONG_TREND
        and plus_di_above_minus_di
    ):
        return "ขาขึ้นแข็งแรง"
    if close_above_sma_20 and sma_20_above_sma_50:
        return "ขาขึ้นระยะสั้น"
    if score <= -1:
        return "อ่อนแรง/ควรระวัง"
    return "sideway หรือยังไม่ยืนยัน"
