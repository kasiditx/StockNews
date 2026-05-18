from __future__ import annotations

from dataclasses import dataclass

from stock_alerts.models import StockReport


@dataclass(frozen=True)
class SopAssessment:
    business_importance: str
    upside_view: str
    news_impact: str
    decision_note: str


def assess_report_with_sop(report: StockReport) -> SopAssessment:
    return SopAssessment(
        business_importance=assess_business_importance(report),
        upside_view=assess_upside_view(report),
        news_impact=assess_news_impact(report),
        decision_note=build_decision_note(report),
    )


def assess_business_importance(report: StockReport) -> str:
    text = f"{report.profile.business} {report.profile.sector or ''} {report.profile.industry or ''}".lower()
    if any(keyword in text for keyword in ("semiconductor", "ai", "artificial intelligence", "chip")):
        return "โครงสร้างพื้นฐาน AI/data center และ supply chain ชิป"
    if any(keyword in text for keyword in ("software", "cloud", "cybersecurity")):
        return "ระบบดิจิทัลขององค์กร, cloud, data และ productivity"
    if any(keyword in text for keyword in ("bank", "finance", "payment", "insurance", "asset management")):
        return "ระบบการเงิน, credit, payment และการหมุนเวียนเงินในเศรษฐกิจ"
    if any(
        keyword in text
        for keyword in (
            "aerospace",
            "defense",
            "machinery",
            "industrial",
            "logistics",
            "transportation",
            "trucking",
        )
    ):
        return "โครงสร้างเศรษฐกิจจริง เช่น การผลิต, ขนส่ง, logistics และความมั่นคง"
    if any(keyword in text for keyword in ("health", "medical", "biotechnology", "drug")):
        return "บริการสุขภาพ ยา และโครงสร้างพื้นฐานทางการแพทย์"
    if any(keyword in text for keyword in ("media", "advertising", "internet", "retail", "travel", "consumer")):
        return "พฤติกรรมผู้บริโภค, แพลตฟอร์มออนไลน์, โฆษณา และบริการรายวัน"
    if any(keyword in text for keyword in ("telecommunication", "communication")):
        return "โครงข่ายสื่อสารและ connectivity สำหรับผู้ใช้/องค์กร"
    return "ธุรกิจในห่วงโซ่เศรษฐกิจของกลุ่มที่คัดไว้ ควรอ่านรายละเอียดเพิ่มก่อนตัดสินใจ"


def assess_upside_view(report: StockReport) -> str:
    opportunity_score = calculate_opportunity_score(report)
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


def assess_news_impact(report: StockReport) -> str:
    strongest_news_score = strongest_news_score_for(report)
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


def build_decision_note(report: StockReport) -> str:
    if report.signal.risk_flags:
        return "ศึกษาต่อได้ แต่ต้องเช็ก risk flags และวาง stop-loss ก่อนคิดเรื่องซื้อ"
    if calculate_opportunity_score(report) >= 7:
        return "เหมาะเป็นตัว shortlist เพื่อหา entry, stop-loss, target และ R/R ต่อ"
    return "เหมาะเฝ้าดูต่อมากกว่าตัดสินใจทันที"


def calculate_opportunity_score(report: StockReport) -> int:
    return report.signal.score + strongest_news_score_for(report)


def strongest_news_score_for(report: StockReport) -> int:
    return max((news_item.sentiment_score for news_item in report.news), default=0)
