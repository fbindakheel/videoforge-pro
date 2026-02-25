"""
main_window.py — Root QMainWindow for VideoForge Pro
"""
import os
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QAction, QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QPushButton, QLabel, QFileDialog, QStatusBar,
    QMessageBox, QFrame, QSizePolicy, QSystemTrayIcon, QMenu,
)

from app.core.ffmpeg_manager import FFmpegManager
from app.core.presets import JobConfig, PresetManager
from app.core.batch_processor import BatchProcessor, BatchJob, JobStatus
from app.core.utils import format_size, seconds_to_hhmmss
from app.core.settings_store import SettingsStore

from app.ui.widgets.drop_zone import DropZone
from app.ui.widgets.file_list import FileListPanel
from app.ui.widgets.settings_panel import SettingsPanel
from app.ui.widgets.progress_panel import ProgressPanel
from app.ui.widgets.video_info_panel import VideoInfoPanel


class MainWindow(QMainWindow):
    """VideoForge Pro — Main window."""

    APP_NAME = "VideoForge Pro"

    def __init__(self):
        super().__init__()
        self._ffmpeg = FFmpegManager()
        self._preset_mgr = PresetManager()
        self._settings_store = SettingsStore()
        self._batch: BatchProcessor | None = None
        self._file_infos: dict[str, object] = {}   # path → VideoInfo
        self._processing = False

        self.setWindowTitle(self.APP_NAME)
        self.resize(1260, 820)
        self.setMinimumSize(900, 600)

        self._setup_central()
        self._setup_toolbar()
        self._setup_statusbar()
        self._setup_tray()
        self._detect_ffmpeg()
        self._restore_settings()

    # ── FFmpeg Detection ──────────────────────────────────────────────────────

    def _detect_ffmpeg(self):
        found = self._ffmpeg.detect()
        if found:
            ver = self._ffmpeg.get_version()
            self._set_status(f"✅  FFmpeg ready  —  {ver}", "#22c55e")
            self._settings_panel.set_hw_encoder_info(self._ffmpeg.hw_encoders)
            self._batch = BatchProcessor(self._ffmpeg.ffmpeg, parent=self)
            self._wire_batch()
        else:
            self._set_status(
                "❌  FFmpeg not found — please install FFmpeg and ensure it's on PATH", "#ef4444"
            )
            self._start_btn.setEnabled(False)

    def _wire_batch(self):
        b = self._batch
        b.job_started.connect(self._on_job_started)
        b.job_progress.connect(self._on_job_progress)
        b.job_log.connect(self._on_job_log)
        b.job_done.connect(self._on_job_done)
        b.job_error.connect(self._on_job_error)
        b.overall_progress.connect(self._progress_panel.set_overall_progress)
        b.batch_done.connect(self._on_batch_done)

    # ── System Tray ───────────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        # Use a built-in Qt icon as fallback (no external icon file required)
        self._tray.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_MediaPlay
        ))
        self._tray.setToolTip(self.APP_NAME)

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self._bring_to_front)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._bring_to_front()

    def _bring_to_front(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _notify_tray(self, title: str, message: str):
        """Show a system tray balloon notification (Windows)."""
        if self._tray.isSystemTrayAvailable():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

    # ── Settings Persistence ──────────────────────────────────────────────────

    def _restore_settings(self):
        """Load last-used settings and apply them to the settings panel."""
        cfg = self._settings_store.load()
        if cfg:
            self._settings_panel.apply_config(cfg)

    def _save_settings(self):
        """Persist current settings before quitting."""
        cfg = self._settings_panel.get_config()
        self._settings_store.save(cfg)

    def closeEvent(self, event):
        """Override to save settings and hide tray on close."""
        self._save_settings()
        self._tray.hide()
        super().closeEvent(event)

    # ── Central Widget ────────────────────────────────────────────────────────

    def _setup_central(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(12, 8, 12, 8)
        root_layout.setSpacing(8)

        # ── Header ──
        header = self._build_header()
        root_layout.addWidget(header)

        # ── Separator ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        root_layout.addWidget(line)

        # ── Main split: left (drop + info + files) | right (settings) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = self._build_left_panel()
        splitter.addWidget(left)

        self._settings_panel = SettingsPanel(self._preset_mgr)
        self._settings_panel.merge_files_requested.connect(self._merge_files)
        self._settings_panel.extract_audio_requested.connect(self._extract_audio)
        splitter.addWidget(self._settings_panel)

        splitter.setSizes([420, 600])
        root_layout.addWidget(splitter, stretch=1)

        # ── Separator ──
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        root_layout.addWidget(line2)

        # ── Progress ──
        self._progress_panel = ProgressPanel()
        root_layout.addWidget(self._progress_panel)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 0, 4, 0)

        icon_lbl = QLabel("🎬")
        icon_lbl.setStyleSheet("font-size: 28px;")

        title = QLabel("<b style='font-size:20px;color:#fff;'>VideoForge</b>"
                       "<span style='font-size:20px;color:#6c63ff;'> Pro</span>")
        subtitle = QLabel("Video compressor, converter & editor")
        subtitle.setStyleSheet("font-size: 11px; color: #94a3b8;")

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        lay.addWidget(icon_lbl)
        lay.addSpacing(8)
        lay.addLayout(title_col)
        lay.addStretch()

        # Quick-action buttons in header
        for text, slot, name in (
            ("➕  Add Files", self._browse_files, "secondary"),
            ("🗂  Open Output", self._open_output_folder, "secondary"),
        ):
            btn = QPushButton(text)
            btn.setObjectName(name)
            btn.setFixedHeight(34)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        return w

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._add_files)
        self._drop_zone.browse_clicked.connect(self._browse_files)
        lay.addWidget(self._drop_zone)

        # ── Video Info Panel (NEW) ──
        self._info_panel = VideoInfoPanel()
        lay.addWidget(self._info_panel)

        self._file_list = FileListPanel()
        self._file_list.files_removed.connect(self._on_file_removed)
        self._file_list.file_selected.connect(self._on_file_selected)
        lay.addWidget(self._file_list, stretch=1)

        return w

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _setup_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        self._start_btn = QPushButton("▶  Start Processing")
        self._start_btn.setObjectName("success")
        self._start_btn.setFixedHeight(34)
        self._start_btn.clicked.connect(self._start_processing)
        tb.addWidget(self._start_btn)

        tb.addSeparator()

        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("danger")
        self._stop_btn.setFixedHeight(34)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_processing)
        tb.addWidget(self._stop_btn)

        tb.addSeparator()

        self._clear_btn = QPushButton("🗑  Clear Queue")
        self._clear_btn.setObjectName("secondary")
        self._clear_btn.setFixedHeight(34)
        self._clear_btn.clicked.connect(self._clear_queue)
        tb.addWidget(self._clear_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self._files_lbl = QLabel("No files loaded")
        self._files_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 0 12px;")
        tb.addWidget(self._files_lbl)

    # ── Status Bar ────────────────────────────────────────────────────────────

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._status_label = QLabel("Starting up…")
        self._statusbar.addWidget(self._status_label, 1)

    def _set_status(self, text: str, color: str = "#94a3b8"):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; font-size: 12px; padding: 2px 8px;")

    # ── File Handling ─────────────────────────────────────────────────────────

    def _browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Video Files",
            str(Path.home()),
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.gif *.m4v *.flv *.wmv *.ts *.3gp);;All Files (*)"
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths: list[str]):
        added = 0
        first_info = None
        for path in paths:
            if path in self._file_infos:
                continue
            info = self._ffmpeg.probe(path) if self._ffmpeg.available else None
            size = os.path.getsize(path) if os.path.exists(path) else 0
            self._file_infos[path] = info
            self._file_list.add_file(path, size)
            added += 1

            # Capture first info for panel / estimate
            if info and first_info is None:
                first_info = info

        # Update info panel and estimate with first newly added file
        if first_info:
            self._info_panel.update_info(first_info)
            self._settings_panel.set_video_info(
                first_info.duration, first_info.width, first_info.height,
                first_info.fps, first_info.file_size
            )

        count = self._file_list.count()
        self._files_lbl.setText(
            f"{count} file{'s' if count != 1 else ''} queued"
        )
        if added:
            self._set_status(f"Added {added} file(s)  —  {count} total in queue")

    def _on_file_removed(self, index: int):
        count = self._file_list.count()
        self._files_lbl.setText(
            f"{count} file{'s' if count != 1 else ''} queued"
            if count else "No files loaded"
        )
        if count == 0:
            self._info_panel.clear()

    def _on_file_selected(self, path: str):
        """Update the info panel when the user clicks a file in the queue."""
        info = self._file_infos.get(path)
        if info:
            self._info_panel.update_info(info)
            self._settings_panel.set_video_info(
                info.duration, info.width, info.height, info.fps, info.file_size
            )

    def _clear_queue(self):
        if self._processing:
            QMessageBox.warning(self, "Processing", "Stop processing before clearing the queue.")
            return
        if self._batch:
            self._batch.clear_all()
        self._file_list.clear_all()
        self._file_infos.clear()
        self._files_lbl.setText("No files loaded")
        self._progress_panel.reset()
        self._info_panel.clear()
        self._set_status("Queue cleared")

    # ── Processing ────────────────────────────────────────────────────────────

    def _start_processing(self):
        if not self._ffmpeg.available:
            QMessageBox.critical(self, "FFmpeg Missing",
                                 "FFmpeg is not installed or not on PATH.\n\n"
                                 "See README.md for installation instructions.")
            return
        if self._file_list.count() == 0:
            QMessageBox.information(self, "No Files", "Please add video files first.")
            return
        if self._processing:
            return

        # Build batch jobs from file list
        self._batch.clear_all()
        config = self._settings_panel.get_config()

        hw_enc = self._ffmpeg.best_hw_encoder() if config.use_hw_accel else None
        config.hw_encoder = hw_enc or ""

        for path in self._file_list.file_paths():
            info = self._file_infos.get(path)
            job = BatchJob(input_path=path, info=info)
            self._batch.add_job(job)

        self._processing = True
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._clear_btn.setEnabled(False)
        self._progress_panel.reset()
        self._set_status("⚡  Processing…", "#f59e0b")

        self._batch.start(config)

    def _stop_processing(self):
        if self._batch:
            self._batch.stop()
        self._processing = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._clear_btn.setEnabled(True)
        self._set_status("⛔  Stopped by user", "#ef4444")

    # ── Batch Signals ─────────────────────────────────────────────────────────

    def _on_job_started(self, index: int):
        jobs = self._batch.jobs
        if 0 <= index < len(jobs):
            name = os.path.basename(jobs[index].input_path)
            self._progress_panel.set_current_file(name)
            self._file_list.update_job_status(index, JobStatus.RUNNING)
            self._set_status(f"⚡  Processing: {name}", "#f59e0b")

    def _on_job_progress(self, index: int, pct: float):
        self._file_list.update_job_status(index, JobStatus.RUNNING, progress=pct)
        self._progress_panel.set_current_progress(pct)

    def _on_job_log(self, index: int, line: str):
        self._progress_panel.append_log(line)

    def _on_job_done(self, index: int, inp: str, out: str):
        jobs = self._batch.jobs
        out_size = jobs[index].output_size if 0 <= index < len(jobs) else 0
        self._file_list.update_job_status(
            index, JobStatus.DONE, progress=100,
            output_size=out_size
        )
        self._set_status(f"✅  Done: {os.path.basename(out)}", "#22c55e")

    def _on_job_error(self, index: int, inp: str, error: str):
        self._file_list.update_job_status(index, JobStatus.ERROR, error=error)
        self._progress_panel.append_log(f"ERROR [{os.path.basename(inp)}]: {error}")

    def _on_batch_done(self):
        self._processing = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._clear_btn.setEnabled(True)
        self._progress_panel.set_idle()

        stats = self._batch.stats()
        self._progress_panel.show_batch_summary(
            stats["done"], stats["errors"], stats["saved_bytes"]
        )
        saved = stats["saved_bytes"]
        msg = f"✅  Batch complete  —  {stats['done']} file(s) processed"
        if saved > 0:
            msg += f"  •  💾 Saved {format_size(saved)}"
        self._set_status(msg, "#22c55e")

        # ── System tray balloon notification ──
        tray_msg = f"{stats['done']} file(s) processed"
        if saved > 0:
            tray_msg += f" — saved {format_size(saved)}"
        if stats["errors"]:
            tray_msg += f" ({stats['errors']} error(s))"
        self._notify_tray("VideoForge Pro — Batch Complete", tray_msg)

    # ── Special Operations ────────────────────────────────────────────────────

    def _extract_audio(self):
        """Switch settings to audio extraction mode and start processing."""
        if self._file_list.count() == 0:
            QMessageBox.information(self, "No Files", "Add video files first.")
            return
        cfg = self._settings_panel.get_config()
        cfg.extract_audio_only = True
        self._settings_panel.apply_config(cfg)
        self._start_processing()

    def _merge_files(self):
        """Allow selecting multiple files to merge."""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select videos to merge",
            str(Path.home()),
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm);;All Files (*)"
        )
        if len(paths) < 2:
            QMessageBox.information(self, "Merge", "Please select at least 2 files to merge.")
            return
        self._add_files(paths)
        QMessageBox.information(self, "Merge",
                                f"{len(paths)} files added.\n"
                                "Press Start Processing — they will be merged into one output.")

    def _open_output_folder(self):
        # Determine the best folder/file to open
        target = None

        # 1. Did we just finish a batch? Select the last output file.
        if self._batch and self._batch.jobs:
            last_job = self._batch.jobs[-1]
            if last_job.status in (JobStatus.DONE, JobStatus.ERROR) and last_job.output_path:
                if os.path.exists(last_job.output_path):
                    target = last_job.output_path

        # 2. Otherwise, open the output folder from settings.
        if not target:
            cfg = self._settings_panel.get_config()
            if cfg.output_folder and os.path.isdir(cfg.output_folder):
                target = cfg.output_folder

        # 3. Otherwise, try the directory of the first input file.
        if not target and self._file_list.count() > 0:
            first_path = self._file_list.file_paths()[0]
            if first_path:
                target = os.path.dirname(first_path)

        # Fallback to home dir
        if not target:
            target = str(Path.home())

        if not os.path.exists(target):
            QMessageBox.information(self, "Output Folder", "Target folder or file does not exist.")
            return

        import subprocess
        if os.name == "nt":
            # On Windows, try to 'select' the file if it's a file, otherwise open dir
            if os.path.isfile(target):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(target)}"')
            else:
                subprocess.Popen(f'explorer "{os.path.normpath(target)}"')
        elif os.name == "posix":
            # macOS / Linux
            opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
            
            # 'open -R' reveals the file in Finder on macOS
            if sys.platform == "darwin" and os.path.isfile(target):
                subprocess.Popen([opener, "-R", target])
            else:
                # If it's a file on Linux, or opening dir on macOS/Linux
                target_dir = os.path.dirname(target) if os.path.isfile(target) else target
                subprocess.Popen([opener, target_dir])
