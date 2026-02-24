"""
video_info_panel.py — Live video metadata card for VideoForge Pro.
Displays rich info (codec, resolution, bitrate, FPS, duration, size)
for the currently selected file in the batch queue.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)

from app.core.ffmpeg_manager import VideoInfo
from app.core.utils import format_size, seconds_to_hhmmss


def _row(label: str, value_widget: QLabel) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setStyleSheet("font-size: 11px; color: #64748b; min-width: 72px;")
    row.addWidget(lbl)
    row.addWidget(value_widget, stretch=1)
    return row


class VideoInfoPanel(QWidget):
    """
    Compact card that shows metadata for the currently selected file.
    Call `update_info(VideoInfo)` to populate, `clear()` to reset.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 0)
        outer.setSpacing(0)

        # ── Card ──
        card = QFrame()
        card.setObjectName("InfoCard")
        card.setStyleSheet("""
            QFrame#InfoCard {
                background-color: #1a1d27;
                border: 1px solid #2d3348;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10, 8, 10, 8)
        card_lay.setSpacing(4)

        # Title row
        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 14px; background: transparent;")
        title = QLabel("File Info")
        title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #a78bfa; "
            "letter-spacing: 1px; text-transform: uppercase; background: transparent;"
        )
        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        card_lay.addLayout(title_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2d3348; background-color: #2d3348; max-height: 1px;")
        card_lay.addWidget(sep)
        card_lay.addSpacing(2)

        # ── Metadata grid ──
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        def _make_val(default="—") -> QLabel:
            lbl = QLabel(default)
            lbl.setStyleSheet(
                "font-size: 12px; color: #e2e8f0; font-weight: 500; background: transparent;"
            )
            return lbl

        def _make_key(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size: 11px; color: #64748b; background: transparent;"
            )
            return lbl

        # Row 0: filename
        self._name_lbl = QLabel("No file selected")
        self._name_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #e2e8f0; background: transparent;"
        )
        self._name_lbl.setWordWrap(True)
        card_lay.addWidget(self._name_lbl)

        # Row pairs (key, value)
        self._duration_val  = _make_val()
        self._resolution_val = _make_val()
        self._fps_val        = _make_val()
        self._vcodec_val     = _make_val()
        self._acodec_val     = _make_val()
        self._bitrate_val    = _make_val()
        self._size_val       = _make_val()
        self._format_val     = _make_val()

        pairs = [
            ("Duration",    self._duration_val),
            ("Resolution",  self._resolution_val),
            ("FPS",         self._fps_val),
            ("Video codec", self._vcodec_val),
            ("Audio codec", self._acodec_val),
            ("Bitrate",     self._bitrate_val),
            ("File size",   self._size_val),
            ("Format",      self._format_val),
        ]
        for r, (key, val) in enumerate(pairs):
            grid.addWidget(_make_key(key), r, 0)
            grid.addWidget(val, r, 1)

        card_lay.addLayout(grid)
        outer.addWidget(card)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_info(self, info: VideoInfo):
        """Populate the panel from a VideoInfo object."""
        import os
        self._name_lbl.setText(os.path.basename(info.path))
        self._duration_val.setText(seconds_to_hhmmss(info.duration))
        self._resolution_val.setText(
            f"{info.width} × {info.height}  ({info.resolution_label})"
            if info.width else "—"
        )
        self._fps_val.setText(f"{info.fps:.2f} fps" if info.fps else "—")
        self._vcodec_val.setText(info.video_codec or "—")
        self._acodec_val.setText(info.audio_codec or ("no audio" if not info.has_audio else "—"))
        self._bitrate_val.setText(f"{info.bitrate_kbps} kbps" if info.bitrate_kbps else "—")
        self._size_val.setText(format_size(info.file_size) if info.file_size else "—")
        self._format_val.setText(info.format_name or "—")

    def clear(self):
        """Reset all labels to default state."""
        self._name_lbl.setText("No file selected")
        for lbl in (
            self._duration_val, self._resolution_val, self._fps_val,
            self._vcodec_val, self._acodec_val, self._bitrate_val,
            self._size_val, self._format_val,
        ):
            lbl.setText("—")
