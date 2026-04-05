"""Dynamic weight management for modality fusion."""
import logging

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "voice": 0.30,
    "face": 0.30,
    "hr": 0.40,
}


def adjust_weights(active_modalities: dict[str, bool]) -> dict[str, float]:
    """
    Adjust weights based on which modalities are active.
    Redistributes weight from inactive modalities proportionally.
    """
    weights = DEFAULT_WEIGHTS.copy()

    inactive_weight = sum(weights[k] for k, v in active_modalities.items() if not v)
    active_keys = [k for k, v in active_modalities.items() if v]

    if not active_keys:
        return {k: 0.0 for k in weights}

    # Redistribute inactive weight
    bonus = inactive_weight / len(active_keys)
    for k in weights:
        if not active_modalities.get(k, False):
            weights[k] = 0.0
        else:
            weights[k] += bonus

    return weights
