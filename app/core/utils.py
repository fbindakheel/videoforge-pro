"""
utils.py — Helper utilities for VideoForge Pro
"""
import os
import re
import time
from pathlib import Path


def format_size(num_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    if num_bytes < 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def estimate_output_size(duration_sec: float, bitrate_kbps: int) -> int:
    """Estimate output file size in bytes from duration and bitrate."""
    if duration_sec <= 0 or bitrate_kbps <= 0:
        return 0
    return int((bitrate_kbps * 1000 / 8) * duration_sec)


def crf_to_bitrate_estimate(crf: int, width: int, height: int, fps: float = 30.0) -> int:
    """
    Very rough bitrate estimate (kbps) for H.264 at a given CRF.
    Used only for size preview, not actual encoding.
    """
    pixels = width * height
    # Empirical formula derived from common bitrate guides
    base = (pixels * fps) / 1_000_000  # Mpixels/s
    # CRF 18 → ~high quality, CRF 28 → ~low quality
    quality_factor = max(0.1, (51 - crf) / 33.0)
    bitrate_kbps = int(base * 200 * quality_factor)
    return max(100, bitrate_kbps)


def generate_output_filename(input_path: str, suffix: str = "_compressed", ext: str = None) -> str:
    """
    Generate a unique output filename next to the input file.
    E.g. /videos/clip.mp4 → /videos/clip_compressed.mp4
    """
    p = Path(input_path)
    out_ext = ext if ext else p.suffix
    if not out_ext.startswith("."):
        out_ext = f".{out_ext}"
    base = p.stem + suffix + out_ext
    out = p.parent / base
    # Avoid overwriting — append counter if needed
    counter = 1
    while out.exists():
        out = p.parent / f"{p.stem}{suffix}_{counter}{out_ext}"
        counter += 1
    return str(out)


def parse_ffmpeg_time(line: str) -> float | None:
    """
    Parse time= field from FFmpeg progress line.
    Returns seconds as float, or None if not found.
    E.g. 'frame= 120 fps=60 q=28 time=00:00:04.00 ...'
    """
    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return None


def seconds_to_hhmmss(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS string."""
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def hhmmss_to_seconds(time_str: str) -> float:
    """Convert HH:MM:SS or MM:SS string to float seconds."""
    parts = time_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except ValueError:
        return 0.0


class ETACalculator:
    """Simple ETA calculator based on progress percentage."""

    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def get_eta(self, progress_pct: float) -> str:
        """Returns ETA string like '~00:01:23' or 'Calculating...'"""
        if self.start_time is None or progress_pct <= 0:
            return "Calculating..."
        elapsed = time.time() - self.start_time
        if progress_pct >= 100:
            return "Done"
        total_estimated = elapsed / (progress_pct / 100.0)
        remaining = total_estimated - elapsed
        return f"~{seconds_to_hhmmss(remaining)}"
