"""
ffmpeg_manager.py — FFmpeg/ffprobe detection and video metadata probing for VideoForge Pro
"""
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoInfo:
    """Metadata about a video file extracted via ffprobe."""
    path: str = ""
    duration: float = 0.0          # seconds
    width: int = 0
    height: int = 0
    fps: float = 30.0
    video_codec: str = ""
    audio_codec: str = ""
    bitrate_kbps: int = 0
    file_size: int = 0             # bytes
    has_audio: bool = True
    format_name: str = ""

    @property
    def resolution_label(self) -> str:
        if self.height >= 2160:
            return "4K (2160p)"
        elif self.height >= 1080:
            return "1080p"
        elif self.height >= 720:
            return "720p"
        elif self.height >= 480:
            return "480p"
        elif self.height >= 360:
            return "360p"
        else:
            return f"{self.width}×{self.height}"


class FFmpegManager:
    """Handles FFmpeg binary detection, capability probing, and video info extraction."""

    def __init__(self):
        self._ffmpeg_path: Optional[str] = None
        self._ffprobe_path: Optional[str] = None
        self._hw_encoders: list[str] = []
        self._detected = False

    # ── Detection ─────────────────────────────────────────────────────────────

    def detect(self) -> bool:
        """
        Detect ffmpeg and ffprobe on PATH (or common install locations).
        Returns True if both are found.
        """
        self._ffmpeg_path = shutil.which("ffmpeg")
        self._ffprobe_path = shutil.which("ffprobe")

        # Windows common locations
        if not self._ffmpeg_path:
            candidates = [
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    self._ffmpeg_path = c
                    break

        if not self._ffprobe_path:
            candidates = [
                r"C:\ffmpeg\bin\ffprobe.exe",
                r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
                os.path.expanduser(r"~\ffmpeg\bin\ffprobe.exe"),
            ]
            for c in candidates:
                if os.path.isfile(c):
                    self._ffprobe_path = c
                    break

        self._detected = bool(self._ffmpeg_path and self._ffprobe_path)
        if self._detected:
            self._probe_hw_encoders()
        return self._detected

    @property
    def available(self) -> bool:
        return self._detected

    @property
    def ffmpeg(self) -> str:
        return self._ffmpeg_path or "ffmpeg"

    @property
    def ffprobe(self) -> str:
        return self._ffprobe_path or "ffprobe"

    @property
    def hw_encoders(self) -> list[str]:
        return self._hw_encoders

    def get_version(self) -> str:
        """Return FFmpeg version string."""
        try:
            result = subprocess.run(
                [self.ffmpeg, "-version"],
                capture_output=True, text=True, timeout=5
            )
            first_line = result.stdout.splitlines()[0] if result.stdout else ""
            return first_line
        except Exception:
            return "Unknown version"

    # ── Hardware Acceleration ─────────────────────────────────────────────────

    def _probe_hw_encoders(self):
        """Detect available hardware video encoders."""
        self._hw_encoders = []
        try:
            result = subprocess.run(
                [self.ffmpeg, "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=10
            )
            encoders_output = result.stdout
            candidates = {
                "h264_nvenc": "NVIDIA NVENC",
                "h264_amf": "AMD AMF",
                "h264_videotoolbox": "Apple VideoToolbox",
                "h264_qsv": "Intel QSV",
                "h264_vaapi": "VA-API",
            }
            for enc, label in candidates.items():
                if enc in encoders_output:
                    self._hw_encoders.append(enc)
        except Exception:
            pass

    def best_hw_encoder(self) -> Optional[str]:
        """Return the best available hardware encoder, or None."""
        return self._hw_encoders[0] if self._hw_encoders else None

    # ── Video Info ────────────────────────────────────────────────────────────

    def probe(self, file_path: str) -> Optional[VideoInfo]:
        """
        Use ffprobe to extract metadata from a video file.
        Returns a VideoInfo dataclass, or None on failure.
        """
        if not self._ffprobe_path:
            return None
        try:
            cmd = [
                self.ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-show_format",
                file_path,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=15, encoding="utf-8", errors="replace"
            )
            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            info = VideoInfo(path=file_path)

            # Parse format
            fmt = data.get("format", {})
            info.duration = float(fmt.get("duration", 0))
            total_bitrate = int(fmt.get("bit_rate", 0))
            info.bitrate_kbps = total_bitrate // 1000
            info.file_size = os.path.getsize(file_path)
            info.format_name = fmt.get("format_long_name", "")

            # Parse streams
            for stream in data.get("streams", []):
                codec_type = stream.get("codec_type", "")
                if codec_type == "video" and not info.video_codec:
                    info.video_codec = stream.get("codec_name", "")
                    info.width = stream.get("width", 0)
                    info.height = stream.get("height", 0)
                    # FPS
                    r_frame = stream.get("r_frame_rate", "30/1")
                    try:
                        num, den = r_frame.split("/")
                        info.fps = float(num) / float(den) if float(den) else 30.0
                    except Exception:
                        info.fps = 30.0
                elif codec_type == "audio":
                    info.audio_codec = stream.get("codec_name", "")
                    info.has_audio = True

            return info

        except Exception:
            return None
