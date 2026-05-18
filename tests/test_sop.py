from __future__ import annotations

from stock_alerts.models import NewsItem, StockProfile, StockReport, TechnicalSignal
from stock_alerts.sop import assess_report_with_sop


def test_sop_assessment_identifies_ai_chip_importance_and_strong_upside() -> None:
    report = _build_report(
        business="Technology / Semiconductors and AI data center infrastructure",
        sector="Technology",
        industry="Semiconductors",
        score=6,
        news_score=3,
        risk_flags=(),
    )

    assessment = assess_report_with_sop(report)

    assert assessment.business_importance == "โครงสร้างพื้นฐาน AI/data center และ supply chain ชิป"
    assert assessment.upside_view.startswith("สูงมาก")
    assert assessment.news_impact.startswith("ข่าวบวกแรง")
    assert "shortlist" in assessment.decision_note


def test_sop_assessment_requires_risk_review_when_flags_exist() -> None:
    report = _build_report(
        business="Finance / Global payment network",
        sector="Finance",
        industry="Payment Network",
        score=5,
        news_score=2,
        risk_flags=("ATR สูง",),
    )

    assessment = assess_report_with_sop(report)

    assert assessment.business_importance == "ระบบการเงิน, credit, payment และการหมุนเวียนเงินในเศรษฐกิจ"
    assert "risk flags" in assessment.decision_note


def _build_report(
    business: str,
    sector: str,
    industry: str,
    score: int,
    news_score: int,
    risk_flags: tuple[str, ...],
) -> StockReport:
    return StockReport(
        profile=StockProfile(
            ticker="TEST",
            name="Test Company",
            business=business,
            sector=sector,
            industry=industry,
        ),
        signal=TechnicalSignal(
            ticker="TEST",
            score=score,
            stance="น่าจับตามองมาก",
            close_price=100.0,
            change_percent=3.0,
            rsi=58.0,
            sma_20=95.0,
            sma_50=90.0,
            macd=1.2,
            macd_signal=1.0,
            adx=28.0,
            atr_percent=2.5,
            bollinger_position=0.8,
            distance_from_high_percent=-2.0,
            trend="ขาขึ้นแข็งแรง",
            reasons=("Momentum ดี",),
            risk_flags=risk_flags,
        ),
        news=(
            NewsItem(
                title="Test catalyst",
                link="https://example.com",
                summary="Guidance raised.",
                sentiment="positive",
                sentiment_score=news_score,
            ),
        ),
    )
