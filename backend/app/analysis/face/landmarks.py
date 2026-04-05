"""Face landmark detection using MediaPipe."""
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-load mediapipe
_face_mesh = None


def _get_face_mesh():
    global _face_mesh
    if _face_mesh is None:
        try:
            import mediapipe as mp
            _face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe FaceMesh initialized")
        except ImportError:
            logger.warning("MediaPipe not installed")
    return _face_mesh


# Key landmark indices for facial feature analysis
LANDMARKS = {
    # Eyebrows
    "left_brow_inner": 107,
    "left_brow_outer": 70,
    "right_brow_inner": 336,
    "right_brow_outer": 300,

    # Eyes
    "left_eye_top": 159,
    "left_eye_bottom": 145,
    "left_eye_inner": 133,
    "left_eye_outer": 33,
    "right_eye_top": 386,
    "right_eye_bottom": 374,
    "right_eye_inner": 362,
    "right_eye_outer": 263,

    # Iris (refined landmarks)
    "left_iris_center": 468,
    "right_iris_center": 473,

    # Nose
    "nose_tip": 1,

    # Mouth
    "mouth_left": 61,
    "mouth_right": 291,
    "mouth_top": 13,
    "mouth_bottom": 14,
    "mouth_inner_top": 82,
    "mouth_inner_bottom": 87,

    # Cheeks
    "left_cheek": 123,
    "right_cheek": 352,
}


def detect_landmarks(frame: np.ndarray) -> dict | None:
    """Detect 468 face landmarks and return key measurements."""
    mesh = _get_face_mesh()
    if mesh is None:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None

    face = results.multi_face_landmarks[0]
    h, w = frame.shape[:2]

    # Extract key points as (x, y) normalized
    points = {}
    for name, idx in LANDMARKS.items():
        if idx < len(face.landmark):
            lm = face.landmark[idx]
            points[name] = (lm.x * w, lm.y * h, lm.z)

    return points


def compute_face_metrics(points: dict) -> dict:
    """Compute meaningful facial metrics from landmarks."""
    if not points:
        return {}

    metrics = {}

    # Eye Aspect Ratio (EAR) for blink detection
    for side in ["left", "right"]:
        top = points.get(f"{side}_eye_top")
        bottom = points.get(f"{side}_eye_bottom")
        inner = points.get(f"{side}_eye_inner")
        outer = points.get(f"{side}_eye_outer")
        if all([top, bottom, inner, outer]):
            vertical = abs(top[1] - bottom[1])
            horizontal = abs(outer[0] - inner[0])
            ear = vertical / (horizontal + 1e-6)
            metrics[f"{side}_ear"] = ear

    metrics["ear_mean"] = np.mean([metrics.get("left_ear", 0), metrics.get("right_ear", 0)])

    # Mouth openness
    top = points.get("mouth_top")
    bottom = points.get("mouth_bottom")
    left = points.get("mouth_left")
    right = points.get("mouth_right")
    if all([top, bottom, left, right]):
        mouth_v = abs(top[1] - bottom[1])
        mouth_h = abs(right[0] - left[0])
        metrics["mouth_open_ratio"] = mouth_v / (mouth_h + 1e-6)

    # Mouth corner positions (for smile detection)
    if left and right:
        metrics["mouth_width"] = abs(right[0] - left[0])
        # Asymmetry
        nose = points.get("nose_tip")
        if nose:
            left_dist = abs(left[0] - nose[0])
            right_dist = abs(right[0] - nose[0])
            metrics["mouth_asymmetry"] = abs(left_dist - right_dist) / (max(left_dist, right_dist) + 1e-6)

    # Brow positions (for AU4, AU1+2)
    for side in ["left", "right"]:
        brow = points.get(f"{side}_brow_inner")
        eye = points.get(f"{side}_eye_top")
        if brow and eye:
            metrics[f"{side}_brow_height"] = abs(brow[1] - eye[1])

    # Cheek raiser indicator (AU6) - distance from cheek to eye
    for side in ["left", "right"]:
        cheek = points.get(f"{side}_cheek")
        eye = points.get(f"{side}_eye_bottom")
        if cheek and eye:
            metrics[f"{side}_cheek_raise"] = abs(cheek[1] - eye[1])

    return metrics
