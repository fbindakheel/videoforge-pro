"""
settings_panel.py — Tabbed settings panel for VideoForge Pro
Tabs: Compression · Resolution · Format · Audio · Trim & Edit · Presets · Filters
"""
import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSlider, QComboBox, QCheckBox, QLineEdit,
    QSpinBox, QPushButton, QGroupBox, QTimeEdit, QFileDialog,
    QDoubleSpinBox, QSizePolicy,
)
from PyQt6.QtCore import QTime

from app.core.presets import JobConfig, PresetManager
from app.core.utils import format_size, estimate_output_size, crf_to_bitrate_estimate


RESOLUTION_OPTIONS = ["Original", "4K (2160p)", "1080p", "720p", "480p", "360p", "Custom"]
FORMAT_OPTIONS     = ["mp4", "mkv", "mov", "avi", "webm", "gif"]
AUDIO_FORMATS      = ["aac", "mp3", "wav", "opus", "copy"]
SPEED_OPTIONS      = ["ultrafast", "fast", "medium", "slow", "veryslow"]
CRF_LABELS         = {0: "Lossless / Max", 18: "Low (best quality)", 23: "Medium (balanced)",
                      28: "High", 32: "Very High (small size)", 51: "Minimum"}
ROTATE_OPTIONS     = ["No rotation", "90° Clockwise", "180°", "90° Counter-CW"]
ROTATE_VALUES      = ["none",        "90cw",           "180",  "90ccw"]


def _make_group(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    grp = QGroupBox(title)
    lay = QVBoxLayout(grp)
    lay.setSpacing(10)
    lay.setContentsMargins(10, 18, 10, 10)
    return grp, lay


class SettingsPanel(QWidget):
    """Tabbed settings panel. Emit config_changed on any change."""

    config_changed = pyqtSignal()
    merge_files_requested = pyqtSignal()
    extract_audio_requested = pyqtSignal()

    def __init__(self, preset_manager: PresetManager, parent=None):
        super().__init__(parent)
        self._preset_mgr = preset_manager
        self._video_duration = 0.0
        self._video_w = 1920
        self._video_h = 1080
        self._video_fps = 30.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._tabs.addTab(self._build_compression_tab(), "🗜 Compress")
        self._tabs.addTab(self._build_resolution_tab(), "📺 Resolution")
        self._tabs.addTab(self._build_format_tab(),     "🔄 Format")
        self._tabs.addTab(self._build_audio_tab(),      "🔊 Audio")
        self._tabs.addTab(self._build_trim_tab(),       "✂️ Trim & Edit")
        self._tabs.addTab(self._build_filters_tab(),    "🎨 Filters")
        self._tabs.addTab(self._build_presets_tab(),    "⭐ Presets")

        layout.addWidget(self._tabs)

    # ── Compression Tab ───────────────────────────────────────────────────────

    def _build_compression_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        grp, glay = _make_group("Compression Level")

        crf_row = QHBoxLayout()
        self._crf_label = QLabel("Medium (Balanced)")
        self._crf_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #a78bfa;")
        self._crf_value_lbl = QLabel("CRF 23")
        self._crf_value_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        crf_row.addWidget(self._crf_label)
        crf_row.addStretch()
        crf_row.addWidget(self._crf_value_lbl)
        glay.addLayout(crf_row)

        self._crf_slider = QSlider(Qt.Orientation.Horizontal)
        self._crf_slider.setRange(0, 51)
        self._crf_slider.setValue(23)
        self._crf_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._crf_slider.setTickInterval(5)
        self._crf_slider.valueChanged.connect(self._on_crf_changed)
        glay.addWidget(self._crf_slider)

        crf_hint = QHBoxLayout()
        for txt in ("Best Quality", "Balanced", "Smallest"):
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size: 10px; color: #6b7280;")
            crf_hint.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft if txt == "Best Quality"
                               else (Qt.AlignmentFlag.AlignCenter if txt == "Balanced"
                                     else Qt.AlignmentFlag.AlignRight))
        glay.addLayout(crf_hint)

        lay.addWidget(grp)

        # Speed preset
        grp2, g2lay = _make_group("Encoding Speed")
        form = QFormLayout()
        form.setSpacing(8)
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["ultrafast", "fast", "medium", "slow", "veryslow"])
        self._speed_combo.setCurrentText("medium")
        self._speed_combo.setToolTip("Slower = better compression at same quality")
        self._speed_combo.currentTextChanged.connect(self._emit)
        form.addRow("Preset:", self._speed_combo)
        g2lay.addLayout(form)
        lay.addWidget(grp2)

        # HW Accel
        grp3, g3lay = _make_group("Hardware Acceleration")
        self._hw_check = QCheckBox("Use GPU encoding (NVENC / AMF / VideoToolbox)")
        self._hw_check.setChecked(True)
        self._hw_check.toggled.connect(self._emit)
        self._hw_label = QLabel("No hardware encoder detected")
        self._hw_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        g3lay.addWidget(self._hw_check)
        g3lay.addWidget(self._hw_label)
        lay.addWidget(grp3)

        # Estimated output size
        grp4, g4lay = _make_group("Estimated Output Size")
        self._est_label = QLabel("—")
        self._est_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._est_label.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #6c63ff; padding: 8px;"
        )
        self._est_sub = QLabel("Select a file to see preview")
        self._est_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._est_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        g4lay.addWidget(self._est_label)
        g4lay.addWidget(self._est_sub)
        lay.addWidget(grp4)

        lay.addStretch()
        return w

    def _on_crf_changed(self, v: int):
        # Update label
        if v <= 0:
            label = "Lossless"
        elif v <= 18:
            label = "Low  (Best Quality)"
        elif v <= 23:
            label = "Medium  (Balanced)"
        elif v <= 32:
            label = "High"
        else:
            label = "Very High  (Smallest File)"
        self._crf_label.setText(label)
        self._crf_value_lbl.setText(f"CRF {v}")
        self._update_size_estimate()
        self._emit()

    # ── Resolution Tab ────────────────────────────────────────────────────────

    def _build_resolution_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        grp, glay = _make_group("Output Resolution")
        form = QFormLayout()
        form.setSpacing(10)

        self._res_combo = QComboBox()
        self._res_combo.addItems(RESOLUTION_OPTIONS)
        self._res_combo.currentTextChanged.connect(self._on_res_changed)
        form.addRow("Preset:", self._res_combo)

        custom_row = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(0, 7680)
        self._width_spin.setValue(1920)
        self._width_spin.setSuffix(" px")
        self._width_spin.setToolTip("0 = auto")
        self._height_spin = QSpinBox()
        self._height_spin.setRange(0, 4320)
        self._height_spin.setValue(1080)
        self._height_spin.setSuffix(" px")
        self._height_spin.setToolTip("0 = auto")
        custom_row.addWidget(QLabel("W:"))
        custom_row.addWidget(self._width_spin)
        custom_row.addWidget(QLabel("H:"))
        custom_row.addWidget(self._height_spin)
        self._custom_res_widget = QWidget()
        self._custom_res_widget.setLayout(custom_row)
        self._custom_res_widget.setVisible(False)
        form.addRow("Custom:", self._custom_res_widget)

        for sp in (self._width_spin, self._height_spin):
            sp.valueChanged.connect(self._emit)

        self._change_res_check = QCheckBox("Apply resolution change")
        self._change_res_check.setChecked(False)
        self._change_res_check.toggled.connect(self._emit)

        glay.addLayout(form)
        glay.addWidget(self._change_res_check)

        self._res_info = QLabel("Original resolution will be kept unless enabled above.")
        self._res_info.setWordWrap(True)
        self._res_info.setStyleSheet("font-size: 11px; color: #94a3b8; padding-top: 6px;")
        glay.addWidget(self._res_info)

        lay.addWidget(grp)
        lay.addStretch()
        return w

    def _on_res_changed(self, text: str):
        is_custom = text == "Custom"
        self._custom_res_widget.setVisible(is_custom)
        self._emit()

    # ── Format Tab ────────────────────────────────────────────────────────────

    def _build_format_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        grp, glay = _make_group("Output Format")
        form = QFormLayout()
        form.setSpacing(10)
        self._format_combo = QComboBox()
        self._format_combo.addItems(FORMAT_OPTIONS)
        self._format_combo.currentTextChanged.connect(self._emit)
        form.addRow("Container:", self._format_combo)
        glay.addLayout(form)

        desc = QLabel(
            "• MP4 — Best compatibility (web, mobile)\n"
            "• MKV — Best for high-quality archives\n"
            "• MOV — Apple / Final Cut workflow\n"
            "• AVI — Legacy player support\n"
            "• WEBM — Web streaming / open codec\n"
            "• GIF — Short animated clips (mute, high color loss)"
        )
        desc.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.6;")
        glay.addWidget(desc)

        lay.addWidget(grp)

        # Output folder
        grp2, g2lay = _make_group("Output Folder")
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        self._folder_edit.setPlaceholderText("Same folder as input (default)")
        self._folder_edit.setReadOnly(True)
        self._folder_btn = QPushButton("Browse…")
        self._folder_btn.setObjectName("secondary")
        self._folder_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self._folder_edit, stretch=1)
        folder_row.addWidget(self._folder_btn)
        g2lay.addLayout(folder_row)
        lay.addWidget(grp2)

        lay.addStretch()
        return w

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if folder:
            self._folder_edit.setText(folder)
            self._emit()

    # ── Audio Tab ─────────────────────────────────────────────────────────────

    def _build_audio_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        grp, glay = _make_group("Audio Settings")
        form = QFormLayout()
        form.setSpacing(10)

        self._audio_format_combo = QComboBox()
        self._audio_format_combo.addItems(AUDIO_FORMATS)
        self._audio_format_combo.currentTextChanged.connect(self._emit)
        form.addRow("Format:", self._audio_format_combo)

        bitrate_row = QHBoxLayout()
        self._audio_bitrate = QSlider(Qt.Orientation.Horizontal)
        self._audio_bitrate.setRange(32, 320)
        self._audio_bitrate.setValue(128)
        self._audio_bitrate.setSingleStep(8)
        self._audio_bitrate_label = QLabel("128 kbps")
        self._audio_bitrate_label.setMinimumWidth(70)
        self._audio_bitrate.valueChanged.connect(
            lambda v: (self._audio_bitrate_label.setText(f"{v} kbps"), self._emit())
        )
        bitrate_row.addWidget(self._audio_bitrate)
        bitrate_row.addWidget(self._audio_bitrate_label)
        bitrate_widget = QWidget()
        bitrate_widget.setLayout(bitrate_row)
        form.addRow("Bitrate:", bitrate_widget)
        glay.addLayout(form)

        self._mute_check = QCheckBox("Remove audio (mute output)")
        self._mute_check.toggled.connect(self._emit)
        self._normalize_check = QCheckBox("Normalize audio levels (loudnorm)")
        self._normalize_check.toggled.connect(self._emit)
        glay.addWidget(self._mute_check)
        glay.addWidget(self._normalize_check)
        lay.addWidget(grp)

        lay.addStretch()
        return w

    # ── Trim & Edit Tab ───────────────────────────────────────────────────────

    def _build_trim_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        # Trim
        grp, glay = _make_group("Trim Video")
        self._trim_check = QCheckBox("Enable trimming")
        self._trim_check.toggled.connect(self._on_trim_toggled)
        glay.addWidget(self._trim_check)

        trim_form = QFormLayout()
        trim_form.setSpacing(8)
        self._trim_start = QLineEdit("00:00:00")
        self._trim_start.setPlaceholderText("HH:MM:SS")
        self._trim_start.setMaximumWidth(120)
        self._trim_end = QLineEdit("00:00:00")
        self._trim_end.setPlaceholderText("HH:MM:SS (0 = end)")
        self._trim_end.setMaximumWidth(120)
        for w2 in (self._trim_start, self._trim_end):
            w2.setEnabled(False)
            w2.textChanged.connect(self._emit)
        trim_form.addRow("Start:", self._trim_start)
        trim_form.addRow("End:", self._trim_end)
        glay.addLayout(trim_form)
        lay.addWidget(grp)

        # GIF
        grp2, g2lay = _make_group("Create GIF")
        self._gif_check = QCheckBox("Create GIF from segment")
        self._gif_check.toggled.connect(self._emit)
        gif_form = QFormLayout()
        gif_form.setSpacing(8)
        self._gif_fps_spin = QSpinBox()
        self._gif_fps_spin.setRange(1, 30)
        self._gif_fps_spin.setValue(10)
        self._gif_fps_spin.valueChanged.connect(self._emit)
        self._gif_width_spin = QSpinBox()
        self._gif_width_spin.setRange(64, 1280)
        self._gif_width_spin.setValue(480)
        self._gif_width_spin.setSuffix(" px")
        self._gif_width_spin.valueChanged.connect(self._emit)
        gif_form.addRow("FPS:", self._gif_fps_spin)
        gif_form.addRow("Width:", self._gif_width_spin)
        g2lay.addWidget(self._gif_check)
        g2lay.addLayout(gif_form)
        lay.addWidget(grp2)

        # Special operations
        grp3, g3lay = _make_group("Special Operations")
        self._extract_audio_btn = QPushButton("🎵  Extract Audio from Video")
        self._extract_audio_btn.setObjectName("secondary")
        self._extract_audio_btn.clicked.connect(self.extract_audio_requested.emit)
        self._merge_btn = QPushButton("🔗  Merge Multiple Videos")
        self._merge_btn.setObjectName("secondary")
        self._merge_btn.clicked.connect(self.merge_files_requested.emit)
        g3lay.addWidget(self._extract_audio_btn)
        g3lay.addWidget(self._merge_btn)
        lay.addWidget(grp3)

        lay.addStretch()
        return w

    def _on_trim_toggled(self, checked: bool):
        self._trim_start.setEnabled(checked)
        self._trim_end.setEnabled(checked)
        self._emit()

    # ── Filters Tab (NEW) ─────────────────────────────────────────────────────

    def _build_filters_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        # ── FPS Limit ──
        grp_fps, glay_fps = _make_group("FPS Limiter")
        self._fps_limit_check = QCheckBox("Limit output frame rate")
        self._fps_limit_check.toggled.connect(self._on_fps_limit_toggled)
        fps_row = QHBoxLayout()
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 120)
        self._fps_spin.setValue(30)
        self._fps_spin.setSuffix(" fps")
        self._fps_spin.setEnabled(False)
        self._fps_spin.valueChanged.connect(self._emit)
        fps_row.addWidget(QLabel("Target FPS:"))
        fps_row.addWidget(self._fps_spin)
        fps_row.addStretch()
        glay_fps.addWidget(self._fps_limit_check)
        glay_fps.addLayout(fps_row)
        lay.addWidget(grp_fps)

        # ── Rotate & Flip ──
        grp_rot, glay_rot = _make_group("Rotate & Flip")
        rot_form = QFormLayout()
        rot_form.setSpacing(8)

        self._rotate_combo = QComboBox()
        self._rotate_combo.addItems(ROTATE_OPTIONS)
        self._rotate_combo.currentTextChanged.connect(self._emit)
        rot_form.addRow("Rotate:", self._rotate_combo)

        flip_row = QHBoxLayout()
        self._flip_h_check = QCheckBox("Flip Horizontal")
        self._flip_h_check.toggled.connect(self._emit)
        self._flip_v_check = QCheckBox("Flip Vertical")
        self._flip_v_check.toggled.connect(self._emit)
        flip_row.addWidget(self._flip_h_check)
        flip_row.addWidget(self._flip_v_check)
        flip_row.addStretch()
        flip_widget = QWidget()
        flip_widget.setLayout(flip_row)
        rot_form.addRow("Flip:", flip_widget)

        glay_rot.addLayout(rot_form)
        lay.addWidget(grp_rot)

        # ── Playback Speed ──
        grp_spd, glay_spd = _make_group("Playback Speed")
        speed_row = QHBoxLayout()
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(25, 400)   # represents 0.25x – 4.0x (* 100)
        self._speed_slider.setValue(100)        # 1.0x
        self._speed_slider.setTickInterval(25)
        self._speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._speed_label = QLabel("1.00×")
        self._speed_label.setMinimumWidth(50)
        self._speed_label.setStyleSheet("font-weight: 600; color: #a78bfa; font-size: 13px;")
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(self._speed_slider, stretch=1)
        speed_row.addWidget(self._speed_label)
        speed_hint = QHBoxLayout()
        for txt in ("0.25×  Slow-Mo", "1×  Normal", "4×  Fast"):
            lbl = QLabel(txt)
            lbl.setStyleSheet("font-size: 10px; color: #6b7280;")
            speed_hint.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft if "Slow" in txt
                                 else (Qt.AlignmentFlag.AlignCenter if "Normal" in txt
                                       else Qt.AlignmentFlag.AlignRight))
        glay_spd.addLayout(speed_row)
        glay_spd.addLayout(speed_hint)
        note = QLabel("⚠  Speeds far from 1× may reduce audio quality (atempo chain)")
        note.setStyleSheet("font-size: 10px; color: #64748b;")
        note.setWordWrap(True)
        glay_spd.addWidget(note)
        lay.addWidget(grp_spd)

        # ── Subtitle Burn-in ──
        grp_sub, glay_sub = _make_group("Subtitle Burn-in")
        self._subtitle_check = QCheckBox("Burn subtitles into video")
        self._subtitle_check.toggled.connect(self._on_subtitle_toggled)
        sub_row = QHBoxLayout()
        self._subtitle_edit = QLineEdit()
        self._subtitle_edit.setPlaceholderText("Path to .srt or .ass file…")
        self._subtitle_edit.setReadOnly(True)
        self._subtitle_edit.setEnabled(False)
        self._subtitle_btn = QPushButton("Browse…")
        self._subtitle_btn.setObjectName("secondary")
        self._subtitle_btn.setEnabled(False)
        self._subtitle_btn.clicked.connect(self._browse_subtitle)
        sub_row.addWidget(self._subtitle_edit, stretch=1)
        sub_row.addWidget(self._subtitle_btn)
        glay_sub.addWidget(self._subtitle_check)
        glay_sub.addLayout(sub_row)
        lay.addWidget(grp_sub)

        lay.addStretch()
        return w

    def _on_fps_limit_toggled(self, checked: bool):
        self._fps_spin.setEnabled(checked)
        self._emit()

    def _on_speed_changed(self, value: int):
        factor = value / 100.0
        self._speed_label.setText(f"{factor:.2f}×")
        self._emit()

    def _on_subtitle_toggled(self, checked: bool):
        self._subtitle_edit.setEnabled(checked)
        self._subtitle_btn.setEnabled(checked)
        self._emit()

    def _browse_subtitle(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Subtitle File", "",
            "Subtitle Files (*.srt *.ass *.ssa *.vtt);;All Files (*)"
        )
        if path:
            self._subtitle_edit.setText(path)
            self._emit()

    # ── Presets Tab ───────────────────────────────────────────────────────────

    def _build_presets_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 12, 8, 8)

        grp, glay = _make_group("Load Preset")
        self._preset_combo = QComboBox()
        self._refresh_presets()
        glay.addWidget(self._preset_combo)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Preset")
        apply_btn.clicked.connect(self._apply_preset)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._delete_preset)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(delete_btn)
        glay.addLayout(btn_row)
        lay.addWidget(grp)

        grp2, g2lay = _make_group("Save Current Settings as Preset")
        self._preset_name_edit = QLineEdit()
        self._preset_name_edit.setPlaceholderText("Preset name…")
        save_btn = QPushButton("💾  Save Preset")
        save_btn.clicked.connect(self._save_preset)
        g2lay.addWidget(self._preset_name_edit)
        g2lay.addWidget(save_btn)
        lay.addWidget(grp2)

        lay.addStretch()
        return w

    def _refresh_presets(self):
        self._preset_combo.clear()
        self._preset_combo.addItems(self._preset_mgr.all_preset_names())

    def _apply_preset(self):
        name = self._preset_combo.currentText()
        cfg = self._preset_mgr.get(name)
        if cfg:
            self.apply_config(cfg)

    def _save_preset(self):
        name = self._preset_name_edit.text().strip()
        if name:
            cfg = self.get_config()
            self._preset_mgr.save_user_preset(name, cfg)
            self._refresh_presets()
            self._preset_name_edit.clear()

    def _delete_preset(self):
        name = self._preset_combo.currentText()
        if not self._preset_mgr.is_builtin(name):
            self._preset_mgr.delete_user_preset(name)
            self._refresh_presets()

    # ── Config Read/Write ─────────────────────────────────────────────────────

    def get_config(self) -> JobConfig:
        """Read all UI fields and return a JobConfig."""
        from app.core.utils import hhmmss_to_seconds
        res_text = self._res_combo.currentText()
        res_map   = {"4K (2160p)": "4K", "1080p": "1080p", "720p": "720p",
                     "480p": "480p", "360p": "360p", "Original": "Original"}

        # Rotate value from combo index
        rot_idx = self._rotate_combo.currentIndex()
        rotate_val = ROTATE_VALUES[rot_idx] if 0 <= rot_idx < len(ROTATE_VALUES) else "none"

        cfg = JobConfig(
            # Compression
            crf            = self._crf_slider.value(),
            preset_speed   = self._speed_combo.currentText(),
            use_hw_accel   = self._hw_check.isChecked(),
            # Resolution
            change_resolution   = self._change_res_check.isChecked(),
            resolution_preset   = res_map.get(res_text, res_text),
            output_width        = self._width_spin.value(),
            output_height       = self._height_spin.value(),
            # Format
            output_format  = self._format_combo.currentText(),
            output_folder  = self._folder_edit.text().strip(),
            # Audio
            audio_format      = self._audio_format_combo.currentText(),
            audio_bitrate_kbps = self._audio_bitrate.value(),
            mute_audio        = self._mute_check.isChecked(),
            normalize_audio   = self._normalize_check.isChecked(),
            # Trim
            trim_enabled   = self._trim_check.isChecked(),
            trim_start     = hhmmss_to_seconds(self._trim_start.text()),
            trim_end       = hhmmss_to_seconds(self._trim_end.text()),
            # GIF
            create_gif     = self._gif_check.isChecked(),
            gif_fps        = self._gif_fps_spin.value(),
            gif_width      = self._gif_width_spin.value(),
            # Filters (NEW)
            fps_limit_enabled = self._fps_limit_check.isChecked(),
            fps_limit         = self._fps_spin.value(),
            rotate            = rotate_val,
            flip_h            = self._flip_h_check.isChecked(),
            flip_v            = self._flip_v_check.isChecked(),
            speed_factor      = self._speed_slider.value() / 100.0,
            subtitle_enabled  = self._subtitle_check.isChecked(),
            subtitle_path     = self._subtitle_edit.text().strip(),
        )
        return cfg

    def apply_config(self, cfg: JobConfig):
        """Push a JobConfig into all UI fields."""
        from app.core.utils import seconds_to_hhmmss
        self._crf_slider.setValue(cfg.crf)
        self._speed_combo.setCurrentText(cfg.preset_speed)
        self._hw_check.setChecked(cfg.use_hw_accel)
        rev_map = {"4K": "4K (2160p)"}
        res_label = rev_map.get(cfg.resolution_preset, cfg.resolution_preset)
        idx = self._res_combo.findText(res_label)
        if idx >= 0:
            self._res_combo.setCurrentIndex(idx)
        self._change_res_check.setChecked(cfg.change_resolution)
        self._width_spin.setValue(cfg.output_width)
        self._height_spin.setValue(cfg.output_height)
        idx2 = self._format_combo.findText(cfg.output_format)
        if idx2 >= 0:
            self._format_combo.setCurrentIndex(idx2)
        if cfg.output_folder:
            self._folder_edit.setText(cfg.output_folder)
        idx3 = self._audio_format_combo.findText(cfg.audio_format)
        if idx3 >= 0:
            self._audio_format_combo.setCurrentIndex(idx3)
        self._audio_bitrate.setValue(cfg.audio_bitrate_kbps)
        self._mute_check.setChecked(cfg.mute_audio)
        self._normalize_check.setChecked(cfg.normalize_audio)
        self._trim_check.setChecked(cfg.trim_enabled)
        self._trim_start.setText(seconds_to_hhmmss(cfg.trim_start))
        self._trim_end.setText(seconds_to_hhmmss(cfg.trim_end))
        self._gif_check.setChecked(cfg.create_gif)
        self._gif_fps_spin.setValue(cfg.gif_fps)
        self._gif_width_spin.setValue(cfg.gif_width)
        # Filters (NEW)
        self._fps_limit_check.setChecked(cfg.fps_limit_enabled)
        self._fps_spin.setValue(cfg.fps_limit if cfg.fps_limit > 0 else 30)
        self._fps_spin.setEnabled(cfg.fps_limit_enabled)
        rot_val = cfg.rotate if cfg.rotate else "none"
        rot_idx = ROTATE_VALUES.index(rot_val) if rot_val in ROTATE_VALUES else 0
        self._rotate_combo.setCurrentIndex(rot_idx)
        self._flip_h_check.setChecked(cfg.flip_h)
        self._flip_v_check.setChecked(cfg.flip_v)
        speed_int = int(cfg.speed_factor * 100)
        self._speed_slider.setValue(max(25, min(400, speed_int)))
        self._subtitle_check.setChecked(cfg.subtitle_enabled)
        self._subtitle_edit.setEnabled(cfg.subtitle_enabled)
        self._subtitle_btn.setEnabled(cfg.subtitle_enabled)
        if cfg.subtitle_path:
            self._subtitle_edit.setText(cfg.subtitle_path)

    def set_hw_encoder_info(self, encoders: list[str]):
        if encoders:
            self._hw_label.setText(f"Detected: {', '.join(encoders)}")
            self._hw_label.setStyleSheet("font-size: 11px; color: #22c55e;")
        else:
            self._hw_label.setText("No hardware encoder found — using CPU (libx264)")
            self._hw_label.setStyleSheet("font-size: 11px; color: #94a3b8;")

    def set_video_info(self, duration: float, width: int, height: int, fps: float, file_size: int):
        self._video_duration = duration
        self._video_w = width
        self._video_h = height
        self._video_fps = fps
        self._update_size_estimate()

    def _update_size_estimate(self):
        crf = self._crf_slider.value()
        est_bitrate = crf_to_bitrate_estimate(crf, self._video_w, self._video_h, self._video_fps)
        est_bytes = estimate_output_size(self._video_duration, est_bitrate)
        if est_bytes > 0:
            self._est_label.setText(format_size(est_bytes))
            self._est_sub.setText(f"≈ {est_bitrate} kbps  •  CRF {crf}")
        else:
            self._est_label.setText("—")
            self._est_sub.setText("Select a file to see preview")

    def _emit(self, *_):
        self.config_changed.emit()
