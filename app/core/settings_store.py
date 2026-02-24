"""
settings_store.py — Persistent settings storage for VideoForge Pro.
Saves/restores the last-used JobConfig between application sessions.
"""
import json
from pathlib import Path

from app.core.presets import JobConfig


class SettingsStore:
    """
    Persists a subset of JobConfig fields to disk so that the last-used
    settings are automatically restored on the next launch.
    """

    STORE_DIR  = Path.home() / ".videoforge"
    STORE_FILE = STORE_DIR / "last_settings.json"

    # Fields that are safe / useful to persist across sessions.
    # We intentionally exclude path fields (input/output/subtitle/watermark)
    # and transient state (merge_inputs, hw_encoder).
    PERSISTENT_FIELDS = {
        "crf", "preset_speed", "use_hw_accel",
        "change_resolution", "output_width", "output_height", "resolution_preset",
        "output_format", "output_folder",
        "audio_format", "audio_bitrate_kbps", "mute_audio", "normalize_audio",
        "trim_enabled",
        "create_gif", "gif_fps", "gif_width",
        "auto_name_suffix",
        # New filter fields
        "fps_limit", "fps_limit_enabled",
        "rotate", "flip_h", "flip_v",
        "speed_factor",
        "subtitle_enabled",
    }

    def save(self, config: JobConfig) -> None:
        """Persist the relevant parts of *config* to disk."""
        try:
            self.STORE_DIR.mkdir(parents=True, exist_ok=True)
            data = {k: v for k, v in config.to_dict().items()
                    if k in self.PERSISTENT_FIELDS}
            with open(self.STORE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass   # Never crash on save failure

    def load(self) -> JobConfig | None:
        """
        Load stored settings and return a JobConfig, or None if no
        settings file exists yet.
        """
        if not self.STORE_FILE.exists():
            return None
        try:
            with open(self.STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return JobConfig.from_dict(data)
        except Exception:
            return None
