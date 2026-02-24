"""
video_processor.py — FFmpeg command builder and threaded job runner for VideoForge Pro
"""
import os
import re
import subprocess
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.presets import JobConfig
from app.core.utils import (
    parse_ffmpeg_time,
    generate_output_filename,
    seconds_to_hhmmss,
    hhmmss_to_seconds,
)


RESOLUTION_MAP = {
    "4K":    (3840, 2160),
    "1080p": (1920, 1080),
    "720p":  (1280, 720),
    "480p":  (854, 480),
    "360p":  (640, 360),
}

FORMAT_CODEC_MAP = {
    "mp4":  {"video": "libx264", "audio": "aac"},
    "mkv":  {"video": "libx264", "audio": "aac"},
    "mov":  {"video": "libx264", "audio": "aac"},
    "avi":  {"video": "libxvid", "audio": "mp3"},
    "webm": {"video": "libvpx-vp9", "audio": "libopus"},
    "gif":  {"video": "gif",      "audio": None},
    "mp3":  {"video": None,       "audio": "libmp3lame"},
    "aac":  {"video": None,       "audio": "aac"},
    "wav":  {"video": None,       "audio": "pcm_s16le"},
    "opus": {"video": None,       "audio": "libopus"},
}

CRF_LEVELS = {
    "Low":    18,   # Best quality
    "Medium": 23,   # Balanced
    "High":   32,   # Smallest size
}

SPEED_PRESETS = {
    "ultrafast": "Fastest (lowest compression)",
    "fast":      "Fast",
    "medium":    "Medium",
    "slow":      "Slow",
    "veryslow":  "Slowest (best compression)",
}

# Maps rotate option names → FFmpeg transpose values
ROTATE_FILTER_MAP = {
    "90cw":  "transpose=1",
    "180":   "transpose=2,transpose=2",
    "90ccw": "transpose=2",
}


class VideoProcessor(QThread):
    """
    Runs a single FFmpeg job in a background thread.
    Emits progress, log, finished, and error signals.
    """

    progress = pyqtSignal(float)      # 0.0 – 100.0
    log = pyqtSignal(str)             # FFmpeg stderr line
    finished = pyqtSignal(str, str)   # (input_path, output_path)
    error = pyqtSignal(str, str)      # (input_path, error_message)

    def __init__(self, config: JobConfig, ffmpeg_path: str, duration: float, parent=None):
        super().__init__(parent)
        self.config = config
        self.ffmpeg_path = ffmpeg_path
        self.duration = duration
        self._process: subprocess.Popen | None = None
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def run(self):
        config = self.config
        try:
            cmd = self._build_command()
            if cmd is None:
                self.error.emit(config.input_path, "Failed to build FFmpeg command.")
                return

            self.log.emit(f"▶ Running: {' '.join(cmd)}")
            self.log.emit("─" * 60)

            self._process = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            for line in self._process.stderr:
                if self._cancelled:
                    break
                line = line.rstrip()
                self.log.emit(line)
                if self.duration > 0:
                    t = parse_ffmpeg_time(line)
                    if t is not None:
                        pct = min(100.0, (t / self.duration) * 100)
                        self.progress.emit(pct)

            self._process.wait()

            if self._cancelled:
                self.error.emit(config.input_path, "Cancelled by user.")
                # Clean up partial output
                if config.output_path and os.path.exists(config.output_path):
                    try:
                        os.remove(config.output_path)
                    except Exception:
                        pass
                return

            if self._process.returncode == 0:
                self.progress.emit(100.0)
                self.finished.emit(config.input_path, config.output_path)
            else:
                self.error.emit(config.input_path, f"FFmpeg exited with code {self._process.returncode}")

        except Exception as e:
            self.error.emit(config.input_path, str(e))

    # ── Command Builder ───────────────────────────────────────────────────────

    @staticmethod
    def _add_audio_codec(cmd: list, codec_name: str, bitrate_kbps: int) -> list:
        """
        Append audio codec args. Always adds '-strict -2' so that old FFmpeg
        builds (pre-2015) that treat 'aac' as experimental still work.
        Harmless on modern FFmpeg.
        """
        cmd += ["-c:a", codec_name]
        if codec_name in ("aac", "libvo_aacenc"):
            cmd += ["-strict", "-2"]
        cmd += ["-b:a", f"{bitrate_kbps}k"]
        return cmd

    def _build_command(self) -> list[str] | None:
        config = self.config
        fmt = config.output_format.lower()
        cmd = [self.ffmpeg_path, "-y"]  # -y = overwrite output

        # ── Trim: input seeking (fast) ──
        if config.trim_enabled and config.trim_start > 0:
            cmd += ["-ss", f"{config.trim_start:.3f}"]

        # ── Input ──
        cmd += ["-i", config.input_path]

        # ── Merge inputs ──
        if config.merge_inputs:
            for inp in config.merge_inputs:
                cmd += ["-i", inp]

        # ── Trim: end ──
        if config.trim_enabled and config.trim_end > 0:
            duration = config.trim_end - config.trim_start
            if duration > 0:
                cmd += ["-t", f"{duration:.3f}"]

        # ── Extract audio only ──
        if config.extract_audio_only:
            cmd += ["-vn"]
            audio_codec_name = FORMAT_CODEC_MAP.get(config.audio_format, {}).get("audio", "aac")
            self._add_audio_codec(cmd, audio_codec_name or "aac", config.audio_bitrate_kbps)
            cmd += [config.output_path]
            return cmd

        # ── GIF creation ──
        if fmt == "gif" or config.create_gif:
            return self._build_gif_command(cmd)

        # ── Merge ──
        if config.merge_inputs:
            return self._build_merge_command(cmd)

        # ── Video codec ──
        codec_info = FORMAT_CODEC_MAP.get(fmt, {"video": "libx264", "audio": "aac"})
        video_codec = codec_info.get("video", "libx264")

        if video_codec:
            # Hardware acceleration override
            if (config.use_hw_accel and config.hw_encoder
                    and fmt in ("mp4", "mkv", "mov")
                    and video_codec == "libx264"):
                video_codec = config.hw_encoder
                cmd += ["-c:v", video_codec]
                # NVENC/AMF use -rc:v and -cq instead of -crf
                if "nvenc" in video_codec or "amf" in video_codec:
                    cmd += ["-rc:v", "vbr", "-cq:v", str(config.crf)]
                else:
                    cmd += ["-c:v", video_codec]
            else:
                cmd += ["-c:v", video_codec]
                if video_codec == "libx264":
                    cmd += ["-crf", str(config.crf)]
                    cmd += ["-preset", config.preset_speed]
                elif video_codec == "libvpx-vp9":
                    cmd += ["-crf", str(config.crf), "-b:v", "0"]

        # ── Build video filters ──────────────────────────────────────────────
        vf_filters = self._build_vf_filters(config)

        # ── Audio filters ──────────────────────────────────────────────────
        af_filters = []
        if config.normalize_audio:
            af_filters.append("dynaudnorm")

        # Speed: audio atempo (must be chained for factors > 2 or < 0.5)
        if config.speed_factor != 1.0:
            af_filters += _build_atempo_chain(config.speed_factor)

        # ── Apply filter chains ──
        if vf_filters:
            cmd += ["-vf", ",".join(vf_filters)]
        if af_filters:
            cmd += ["-af", ",".join(af_filters)]

        # ── Audio codec ──
        if config.mute_audio:
            cmd += ["-an"]
        else:
            audio_codec_name = codec_info.get("audio")
            if audio_codec_name:
                if config.audio_format and config.audio_format != "copy":
                    audio_enc = FORMAT_CODEC_MAP.get(config.audio_format, {}).get("audio", "aac")
                    self._add_audio_codec(cmd, audio_enc or "aac", config.audio_bitrate_kbps)
                else:
                    self._add_audio_codec(cmd, audio_codec_name, config.audio_bitrate_kbps)
            else:
                cmd += ["-an"]

        # ── Watermark ──
        if config.watermark_path and os.path.exists(config.watermark_path):
            cmd += ["-i", config.watermark_path]
            position_map = {
                "topleft":     "10:10",
                "topright":    "W-w-10:10",
                "bottomleft":  "10:H-h-10",
                "bottomright": "W-w-10:H-h-10",
            }
            pos = position_map.get(config.watermark_position, "W-w-10:H-h-10")
            cmd += ["-filter_complex", f"overlay={pos}"]

        # ── Format-specific flags ──
        if fmt == "mp4":
            cmd += ["-movflags", "+faststart"]
        elif fmt == "webm":
            cmd += ["-deadline", "good"]

        cmd += [config.output_path]
        return cmd

    # ── Video filter builder ──────────────────────────────────────────────────

    @staticmethod
    def _build_vf_filters(config: JobConfig) -> list[str]:
        """Collect all -vf filter strings for this config."""
        filters = []

        # Resolution scaling
        if config.change_resolution:
            w, h = config.output_width, config.output_height
            if config.resolution_preset in RESOLUTION_MAP:
                w, h = RESOLUTION_MAP[config.resolution_preset]
            if w > 0 and h > 0:
                filters.append(f"scale={w}:{h}:flags=lanczos")
            elif w > 0:
                filters.append(f"scale={w}:-2:flags=lanczos")
            elif h > 0:
                filters.append(f"scale=-2:{h}:flags=lanczos")

        # FPS limit
        if config.fps_limit_enabled and config.fps_limit > 0:
            filters.append(f"fps={config.fps_limit}")

        # Rotate
        if config.rotate and config.rotate != "none":
            rotate_f = ROTATE_FILTER_MAP.get(config.rotate)
            if rotate_f:
                filters.append(rotate_f)

        # Flip
        if config.flip_h:
            filters.append("hflip")
        if config.flip_v:
            filters.append("vflip")

        # Speed (video part: setpts)
        if config.speed_factor != 1.0:
            pts_factor = 1.0 / config.speed_factor
            filters.append(f"setpts={pts_factor:.4f}*PTS")

        # Subtitle burn-in
        if config.subtitle_enabled and config.subtitle_path:
            safe_path = config.subtitle_path.replace("\\", "/").replace(":", "\\:")
            filters.append(f"subtitles='{safe_path}'")

        return filters

    def _build_gif_command(self, base_cmd: list) -> list:
        """Build a high-quality GIF using the palette generation technique."""
        cfg = self.config
        w = cfg.gif_width or 480
        fps = cfg.gif_fps or 10

        scale_filter = f"scale={w}:-1:flags=lanczos"
        palette_filter = (
            f"[v] {scale_filter},fps={fps},split [a][b];"
            f"[a] palettegen [p];"
            f"[b][p] paletteuse"
        )

        cmd = list(base_cmd)
        cmd += ["-filter_complex", palette_filter]
        cmd += [cfg.output_path]
        return cmd

    def _build_merge_command(self, base_cmd: list) -> list:
        """Build concat merge command using filter_complex."""
        cfg = self.config
        n = 1 + len(cfg.merge_inputs)
        cmd = list(base_cmd)
        filter_parts = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        cmd += [
            "-filter_complex",
            f"{filter_parts}concat=n={n}:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
        ]
        cmd += [cfg.output_path]
        return cmd


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_atempo_chain(factor: float) -> list[str]:
    """
    FFmpeg's atempo filter only accepts values in [0.5, 100.0].
    For factors outside that range, chain multiple atempo filters.
    """
    filters = []
    remaining = factor
    # Handle slow-down: chain 0.5 steps
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    # Handle speed-up: chain 2.0 steps until within range
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    filters.append(f"atempo={remaining:.4f}")
    return filters


def build_output_path(config: JobConfig, input_path: str) -> str:
    """
    Determine the output file path for a job.
    Uses config.output_folder if set, otherwise same directory as input.
    """
    ext = config.output_format
    if config.extract_audio_only:
        ext = config.audio_format

    suffix = config.auto_name_suffix or "_vf"
    if config.output_folder:
        p = Path(input_path)
        base = p.stem + suffix + f".{ext}"
        out = Path(config.output_folder) / base
        # Avoid collisions
        counter = 1
        while out.exists():
            out = Path(config.output_folder) / f"{p.stem}{suffix}_{counter}.{ext}"
            counter += 1
        return str(out)
    else:
        return generate_output_filename(input_path, suffix, ext)
