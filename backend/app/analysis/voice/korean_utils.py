"""Korean language specific utilities for speech analysis."""


# Korean filler words (채움말)
KOREAN_FILLERS = [
    "어", "음", "그", "그러니까", "뭐", "이제", "저", "저기",
    "아", "에", "응", "그래서", "그냥", "좀", "이거",
]

# Korean hesitation markers
KOREAN_HESITATION = [
    "글쎄", "글쎄요", "그게", "뭐랄까", "어떻게",
]


def count_fillers(transcript: str) -> int:
    """Count Korean filler words in transcript."""
    count = 0
    words = transcript.split()
    for word in words:
        clean = word.strip(".,!?~")
        if clean in KOREAN_FILLERS:
            count += 1
    return count


def count_hesitations(transcript: str) -> int:
    """Count hesitation markers."""
    count = 0
    for marker in KOREAN_HESITATION:
        if marker in transcript:
            count += 1
    return count


def estimate_syllable_rate(transcript: str, duration_sec: float) -> float:
    """
    Estimate syllable rate for Korean.
    Korean is a syllable-timed language, so syllable rate is more
    meaningful than word rate.
    """
    if duration_sec <= 0:
        return 0.0
    # Each Korean character (except spaces/punctuation) is roughly one syllable
    syllables = sum(1 for c in transcript if '\uAC00' <= c <= '\uD7A3')
    return syllables / duration_sec


def analyze_transcript(transcript: str, duration_sec: float) -> dict:
    """Full Korean speech analysis on transcript."""
    return {
        "filler_count": count_fillers(transcript),
        "hesitation_count": count_hesitations(transcript),
        "syllable_rate": estimate_syllable_rate(transcript, duration_sec),
        "word_count": len(transcript.split()),
        "char_count": len(transcript),
    }
