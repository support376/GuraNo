"""Generate heart rate charts for reports."""
import logging
import os
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


def generate_hr_chart(
    hr_timeline: dict,
    baseline_hr: float | None,
    session_id: str,
    output_dir: str,
) -> str | None:
    """Generate a heart rate timeline chart using matplotlib."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
    except ImportError:
        logger.warning("matplotlib not available")
        return None

    timestamps = hr_timeline.get("timestamps", [])
    bpm_values = hr_timeline.get("bpm", [])

    if not timestamps or not bpm_values:
        return None

    # Convert timestamps to relative seconds
    t0 = timestamps[0]
    times = [(t - t0) for t in timestamps]

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#0f172a')

    # Plot HR line
    ax.plot(times, bpm_values, color='#ef4444', linewidth=2, alpha=0.9)
    ax.fill_between(times, bpm_values, alpha=0.1, color='#ef4444')

    # Baseline
    if baseline_hr:
        ax.axhline(y=baseline_hr, color='#3b82f6', linestyle='--', alpha=0.7, label=f'기준선 ({baseline_hr:.0f} BPM)')

    ax.set_xlabel('시간 (초)', color='#94a3b8', fontsize=10)
    ax.set_ylabel('심박수 (BPM)', color='#94a3b8', fontsize=10)
    ax.tick_params(colors='#64748b')
    ax.spines['bottom'].set_color('#334155')
    ax.spines['left'].set_color('#334155')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if baseline_hr:
        ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#94a3b8')

    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"hr_chart_{session_id}.png")
    plt.savefig(filepath, dpi=150, facecolor=fig.get_facecolor())
    plt.close()

    logger.info(f"HR chart saved: {filepath}")
    return filepath
