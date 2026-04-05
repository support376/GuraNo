"""Action Unit detection from facial metrics."""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AUDetection:
    au_id: str
    name: str
    intensity: float  # 0.0 to 1.0
    active: bool


def detect_action_units(metrics: dict, baseline_metrics: dict | None = None) -> list[AUDetection]:
    """
    Detect FACS Action Units from facial metrics.
    Uses relative changes from baseline where available.
    """
    aus = []
    base = baseline_metrics or {}

    # AU4: Brow Lowerer - brow height decreases
    left_bh = metrics.get("left_brow_height", 0)
    right_bh = metrics.get("right_brow_height", 0)
    base_left_bh = base.get("left_brow_height", left_bh)
    base_right_bh = base.get("right_brow_height", right_bh)

    brow_drop = 0.0
    if base_left_bh > 0:
        brow_drop = max(0, (base_left_bh - left_bh) / base_left_bh)
    au4_intensity = min(brow_drop * 2, 1.0)
    aus.append(AUDetection("AU4", "Brow Lowerer", au4_intensity, au4_intensity > 0.3))

    # AU6: Cheek Raiser - cheek-to-eye distance decreases
    left_cr = metrics.get("left_cheek_raise", 0)
    base_left_cr = base.get("left_cheek_raise", left_cr)
    cheek_raise = 0.0
    if base_left_cr > 0:
        cheek_raise = max(0, (base_left_cr - left_cr) / base_left_cr)
    au6_intensity = min(cheek_raise * 2, 1.0)
    aus.append(AUDetection("AU6", "Cheek Raiser", au6_intensity, au6_intensity > 0.3))

    # AU12: Lip Corner Puller (smile) - mouth width increases
    mouth_w = metrics.get("mouth_width", 0)
    base_mouth_w = base.get("mouth_width", mouth_w)
    smile = 0.0
    if base_mouth_w > 0:
        smile = max(0, (mouth_w - base_mouth_w) / base_mouth_w)
    au12_intensity = min(smile * 3, 1.0)
    aus.append(AUDetection("AU12", "Lip Corner Puller", au12_intensity, au12_intensity > 0.3))

    # AU14: Dimpler - mouth asymmetry
    asymmetry = metrics.get("mouth_asymmetry", 0)
    au14_intensity = min(asymmetry * 3, 1.0)
    aus.append(AUDetection("AU14", "Dimpler", au14_intensity, au14_intensity > 0.3))

    # AU15: Lip Corner Depressor - mouth corners go down
    # Detected indirectly through mouth_open_ratio changes
    mouth_ratio = metrics.get("mouth_open_ratio", 0)
    base_ratio = base.get("mouth_open_ratio", mouth_ratio)
    corner_dep = max(0, (mouth_ratio - base_ratio) / (base_ratio + 1e-6)) if mouth_ratio > base_ratio else 0
    au15_intensity = min(corner_dep, 1.0)
    aus.append(AUDetection("AU15", "Lip Corner Depressor", au15_intensity, au15_intensity > 0.3))

    # AU24: Lip Pressor - mouth_open_ratio very low (pressed lips)
    lip_press = max(0, 1.0 - mouth_ratio * 10) if mouth_ratio < 0.1 else 0
    au24_intensity = min(lip_press, 1.0)
    aus.append(AUDetection("AU24", "Lip Pressor", au24_intensity, au24_intensity > 0.3))

    return aus


def check_fake_smile(aus: list[AUDetection]) -> bool:
    """Detect non-Duchenne smile: AU12 active without AU6."""
    au12 = next((a for a in aus if a.au_id == "AU12"), None)
    au6 = next((a for a in aus if a.au_id == "AU6"), None)
    if au12 and au12.active and (not au6 or not au6.active):
        return True
    return False
