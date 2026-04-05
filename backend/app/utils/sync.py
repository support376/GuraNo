"""Timestamp synchronization utilities."""
import time


class TimestampSync:
    """Synchronize timestamps from different sources (video, audio, HR)."""

    def __init__(self):
        self.offsets: dict[str, float] = {}
        self.reference_time = time.time()

    def register_source(self, source: str, first_timestamp: float):
        """Register a data source's first timestamp for offset calculation."""
        self.offsets[source] = self.reference_time - first_timestamp

    def normalize(self, source: str, timestamp: float) -> float:
        """Normalize a timestamp to reference time."""
        offset = self.offsets.get(source, 0)
        return timestamp + offset

    def get_relative_time(self, timestamp: float) -> float:
        """Get time relative to session start."""
        return timestamp - self.reference_time
