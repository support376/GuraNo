"""Confidence calculation and verdict determination."""
from app.config import settings


def get_verdict(fusion_score: float) -> str:
    if fusion_score >= settings.lie_threshold:
        return "거짓"
    elif fusion_score >= settings.suspect_threshold:
        return "의심"
    return "진실"


def get_verdict_en(fusion_score: float) -> str:
    if fusion_score >= settings.lie_threshold:
        return "lie"
    elif fusion_score >= settings.suspect_threshold:
        return "suspect"
    return "truth"


def confidence_to_percentage(score: float) -> float:
    return round(score * 100, 1)
