"""Multimodal fusion engine - combines voice, face, and heart rate scores."""
import logging
import os
import pickle

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "saved_models", "fusion_lr.pkl")

# Default weights when no trained model is available
DEFAULT_WEIGHTS = {
    "voice": 0.30,
    "face": 0.30,
    "hr": 0.40,
}


class FusionEngine:
    def __init__(self):
        self.model = None
        self.weights = DEFAULT_WEIGHTS.copy()
        self._load_model()

    def _load_model(self):
        """Try to load trained fusion model, fall back to default weights."""
        try:
            if os.path.exists(MODEL_PATH):
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                logger.info("Loaded trained fusion model")

                # Extract weights from logistic regression coefficients
                if hasattr(self.model, "coef_"):
                    coefs = np.abs(self.model.coef_[0])
                    total = np.sum(coefs)
                    if total > 0:
                        self.weights = {
                            "voice": float(coefs[0] / total),
                            "face": float(coefs[1] / total),
                            "hr": float(coefs[2] / total),
                        }
            else:
                logger.info("No trained fusion model found, using default weights")
        except Exception as e:
            logger.warning(f"Failed to load fusion model: {e}")

    def fuse(self, voice_score: float, face_score: float, hr_score: float) -> dict:
        """
        Fuse three modality scores into a single lie probability.

        Args:
            voice_score: P(lie|voice) from VoiceAnalyzer
            face_score: P(lie|face) from FaceAnalyzer
            hr_score: P(lie|hr) from HRAnalyzer

        Returns:
            dict with fusion_score, modality_contributions, etc.
        """
        scores = np.array([voice_score, face_score, hr_score])

        # Count active modalities (score > 0)
        active = scores > 0
        n_active = np.sum(active)

        if n_active == 0:
            return {
                "fusion_score": 0.0,
                "modality_contributions": {"voice": 0, "face": 0, "hr": 0},
                "active_modalities": 0,
            }

        if self.model is not None:
            try:
                # Use trained model
                X = scores.reshape(1, -1)
                proba = self.model.predict_proba(X)[0][1]
                fusion_score = float(proba)
            except Exception:
                fusion_score = self._weighted_average(scores, active)
        else:
            fusion_score = self._weighted_average(scores, active)

        # Compute contributions
        w = np.array([self.weights["voice"], self.weights["face"], self.weights["hr"]])
        contributions = scores * w
        total_contribution = np.sum(contributions)
        if total_contribution > 0:
            contributions = contributions / total_contribution

        return {
            "fusion_score": fusion_score,
            "modality_contributions": {
                "voice": float(contributions[0]),
                "face": float(contributions[1]),
                "hr": float(contributions[2]),
            },
            "active_modalities": int(n_active),
            "weights": self.weights,
        }

    def _weighted_average(self, scores: np.ndarray, active: np.ndarray) -> float:
        """Weighted average fusion with active modality normalization."""
        w = np.array([self.weights["voice"], self.weights["face"], self.weights["hr"]])

        # Zero out weights for inactive modalities and renormalize
        w = w * active.astype(float)
        total_w = np.sum(w)
        if total_w > 0:
            w = w / total_w

        return float(np.sum(scores * w))
