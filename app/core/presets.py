"""
presets.py — Job configuration dataclass and preset management for VideoForge Pro
"""
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class JobConfig:
    """Complete configuration for a single processing job."""
    # Input/Output
    input_path: str = ""
    output_path: str = ""
    output_folder: str = ""

    # Compression
    crf: int = 23                  # H.264 CRF (18=best, 28=small)
    preset_speed: str = "medium"   # FFmpeg preset (ultrafast → veryslow)
    use_hw_accel: bool = True
    hw_encoder: str = ""           # e.g. h264_nvenc, h264_amf, h264_videotoolbox

    # Resolution
    change_resolution: bool = False
    output_width: int = 0          # 0 = keep original
    output_height: int = 0         # 0 = keep original
    resolution_preset: str = "Original"  # "4K", "1080p", "720p", "480p", "Custom"

    # Format
    output_format: str = "mp4"     # mp4, mkv, mov, avi, webm, gif

    # Audio
    audio_format: str = "aac"      # aac, mp3, wav, opus, copy, none
    audio_bitrate_kbps: int = 128
    mute_audio: bool = False
    normalize_audio: bool = False

    # Trim
    trim_enabled: bool = False
    trim_start: float = 0.0        # seconds
    trim_end: float = 0.0          # 0 = no trim end

    # Special operations
    extract_audio_only: bool = False
    create_gif: bool = False
    gif_fps: int = 10
    gif_width: int = 480

    # Merge (handled separately, list of paths)
    merge_inputs: list = field(default_factory=list)

    # Watermark
    watermark_path: str = ""
    watermark_position: str = "bottomright"  # topleft, topright, bottomleft, bottomright

    # Auto-naming
    auto_name_suffix: str = "_vf"

    # ── NEW: Video Filters ──────────────────────────────────────────────────
    fps_limit: int = 0             # 0 = no limit; e.g. 24, 30, 60
    fps_limit_enabled: bool = False

    rotate: str = "none"           # none | 90cw | 180 | 90ccw
    flip_h: bool = False           # horizontal flip
    flip_v: bool = False           # vertical flip

    speed_factor: float = 1.0      # 0.25 – 4.0; 1.0 = no change

    subtitle_path: str = ""        # .srt or .ass path for burn-in
    subtitle_enabled: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JobConfig":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ── Built-in presets ──────────────────────────────────────────────────────────

BUILTIN_PRESETS: dict[str, dict] = {
    "WhatsApp Size": {
        "crf": 32,
        "preset_speed": "fast",
        "change_resolution": True,
        "resolution_preset": "480p",
        "output_width": 640,
        "output_height": 480,
        "output_format": "mp4",
        "audio_format": "aac",
        "audio_bitrate_kbps": 64,
        "mute_audio": False,
        "normalize_audio": False,
        "auto_name_suffix": "_whatsapp",
    },
    "Email Size": {
        "crf": 35,
        "preset_speed": "fast",
        "change_resolution": True,
        "resolution_preset": "480p",
        "output_width": 640,
        "output_height": 480,
        "output_format": "mp4",
        "audio_format": "aac",
        "audio_bitrate_kbps": 64,
        "mute_audio": False,
        "normalize_audio": True,
        "auto_name_suffix": "_email",
    },
    "YouTube 1080p": {
        "crf": 18,
        "preset_speed": "slow",
        "change_resolution": True,
        "resolution_preset": "1080p",
        "output_width": 1920,
        "output_height": 1080,
        "output_format": "mp4",
        "audio_format": "aac",
        "audio_bitrate_kbps": 192,
        "mute_audio": False,
        "normalize_audio": True,
        "auto_name_suffix": "_yt1080p",
    },
    "Instagram Reel": {
        "crf": 22,
        "preset_speed": "medium",
        "change_resolution": True,
        "resolution_preset": "Custom",
        "output_width": 1080,
        "output_height": 1920,
        "output_format": "mp4",
        "audio_format": "aac",
        "audio_bitrate_kbps": 128,
        "mute_audio": False,
        "normalize_audio": True,
        "fps_limit": 30,
        "fps_limit_enabled": True,
        "auto_name_suffix": "_reel",
    },
    "Twitter / X GIF": {
        "crf": 28,
        "preset_speed": "medium",
        "change_resolution": True,
        "resolution_preset": "Custom",
        "output_width": 480,
        "output_height": 0,
        "output_format": "gif",
        "mute_audio": True,
        "trim_enabled": True,
        "trim_start": 0,
        "trim_end": 15,
        "create_gif": True,
        "gif_fps": 12,
        "gif_width": 480,
        "auto_name_suffix": "_twitter",
    },
    "Extract Audio (MP3)": {
        "extract_audio_only": True,
        "audio_format": "mp3",
        "audio_bitrate_kbps": 192,
        "output_format": "mp3",
        "auto_name_suffix": "_audio",
    },
    "Podcast Audio (WAV)": {
        "extract_audio_only": True,
        "audio_format": "wav",
        "audio_bitrate_kbps": 192,
        "output_format": "wav",
        "normalize_audio": True,
        "auto_name_suffix": "_podcast",
    },
    "High Quality Archive": {
        "crf": 18,
        "preset_speed": "veryslow",
        "output_format": "mkv",
        "audio_format": "aac",
        "audio_bitrate_kbps": 256,
        "normalize_audio": False,
        "auto_name_suffix": "_hq",
    },
}


# ── Preset Manager ────────────────────────────────────────────────────────────

class PresetManager:
    """Manages built-in and user-saved presets, persisted to disk."""

    PRESETS_DIR = Path.home() / ".videoforge"
    PRESETS_FILE = PRESETS_DIR / "presets.json"

    def __init__(self):
        self._user_presets: dict[str, dict] = {}
        self._load()

    def _load(self):
        """Load user presets from disk."""
        if self.PRESETS_FILE.exists():
            try:
                with open(self.PRESETS_FILE, "r", encoding="utf-8") as f:
                    self._user_presets = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._user_presets = {}

    def _save(self):
        """Save user presets to disk."""
        self.PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._user_presets, f, indent=2)

    def all_preset_names(self) -> list[str]:
        """Returns all preset names (built-in first, then user)."""
        names = list(BUILTIN_PRESETS.keys())
        for name in self._user_presets:
            if name not in names:
                names.append(name)
        return names

    def get(self, name: str) -> JobConfig | None:
        """Get a JobConfig from a preset name."""
        data = BUILTIN_PRESETS.get(name) or self._user_presets.get(name)
        if data is None:
            return None
        return JobConfig.from_dict(data)

    def save_user_preset(self, name: str, config: JobConfig):
        """Save a user preset."""
        self._user_presets[name] = config.to_dict()
        self._save()

    def delete_user_preset(self, name: str) -> bool:
        """Delete a user preset. Returns True if deleted."""
        if name in self._user_presets:
            del self._user_presets[name]
            self._save()
            return True
        return False

    def is_builtin(self, name: str) -> bool:
        return name in BUILTIN_PRESETS
