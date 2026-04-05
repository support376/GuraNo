"""Generate Korean explanations for lie detection verdicts."""


def generate_reasons(
    voice_result: dict,
    face_result: dict,
    hr_result: dict,
    fusion_score: float,
) -> list[str]:
    """Generate human-readable Korean reasons for a lie detection."""
    reasons = []

    # Voice reasons
    voice_score = voice_result.get("lie_probability", 0)
    if voice_score > 0.3:
        features = voice_result.get("features", {})
        pitch_change = voice_result.get("pitch_change_pct", 0)

        if pitch_change > 5:
            reasons.append(f"음성 피치가 기준선 대비 {pitch_change:.0f}% 상��")
        if features.get("pause_max_duration", 0) > 1.5:
            reasons.append(f"답변 전 비정상적으로 긴 쉼 ({features['pause_max_duration']:.1f}초) 감지")
        if features.get("speech_rate", 0) > 0:
            rate = features.get("speech_rate", 0)
            reasons.append(f"말 속도 감소 감지 (현재: {rate:.1f})")
        if features.get("jitter", 0) > 0.03:
            reasons.append("음성 떨림(Jitter) 증가 감지")

    # Face reasons
    face_score = face_result.get("lie_probability", 0)
    if face_score > 0.3:
        if face_result.get("fake_smile"):
            reasons.append("비진성 미소 탐지 (입만 웃고 눈 주변 근육 비활성)")

        micro_exprs = face_result.get("micro_expressions", [])
        for me in micro_exprs[:2]:
            reasons.append(f"미세표정 탐지: {me['type']} ({me['duration_ms']:.0f}ms)")

        if face_result.get("blink_rate", 0) > 25:
            reasons.append(f"눈 깜빡임 빈도 증가 (분당 {face_result['blink_rate']:.0f}회)")

        if face_result.get("mouth_asymmetry", 0) > 0.15:
            reasons.append("얼굴 표정 비대칭 감지")

    # HR reasons
    hr_score = hr_result.get("lie_probability", 0)
    if hr_score > 0.3:
        hr_increase = hr_result.get("hr_increase", 0)
        if hr_increase > 3:
            reasons.append(f"심박수 기준선 대비 {hr_increase:.0f} BPM 상승")

        hrv = hr_result.get("hrv", {})
        if hrv.get("rmssd", 0) > 0:
            reasons.append(f"심박 변이도(HRV) 변화 감지 (RMSSD: {hrv['rmssd']:.1f}ms)")

        zscore = hr_result.get("zscore", 0)
        if zscore > 1.5:
            reasons.append(f"심박수 이상 탐지 (Z-score: {zscore:.1f})")

    if not reasons:
        reasons.append("종합 분석 결과 거짓 가능성 감지")

    return reasons
