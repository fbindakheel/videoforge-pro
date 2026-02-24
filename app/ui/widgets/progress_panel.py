"""
progress_panel.py — Progress display widget for VideoForge Pro
Shows overall progress bar, per-file progress, ETA, and real-time FFmpeg log.
"""
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QTextEdit, QPushButton, QFileDialog,
)
from app.core.utils import ETACalculator, format_size


class ProgressPanel(QWidget):
    """
    Bottom panel showing:
      - Overall batch progress bar + percentage
      - Current file name + per-file progress bar
      - ETA label
      - Scrollable FFmpeg log (colour-coded) with Save/Collapse controls
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._eta = ETACalculator()
        self._log_collapsed = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Overall progress row ──
        top = QHBoxLayout()
        top.setSpacing(10)

        self._overall_label = QLabel("Overall:")
        self._overall_label.setStyleSheet("font-weight: 600; color: #e2e8f0; font-size: 13px;")
        self._overall_label.setMinimumWidth(70)

        self._overall_bar = QProgressBar()
        self._overall_bar.setRange(0, 100)
        self._overall_bar.setValue(0)
        self._overall_bar.setTextVisible(False)
        self._overall_bar.setFixedHeight(12)

        self._overall_pct = QLabel("0%")
        self._overall_pct.setMinimumWidth(40)
        self._overall_pct.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._overall_pct.setStyleSheet("color: #a78bfa; font-weight: 600;")

        self._eta_label = QLabel("ETA: —")
        self._eta_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self._eta_label.setMinimumWidth(120)
        self._eta_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        top.addWidget(self._overall_label)
        top.addWidget(self._overall_bar, stretch=1)
        top.addWidget(self._overall_pct)
        top.addWidget(self._eta_label)
        layout.addLayout(top)

        # ── Current file row ──
        cur = QHBoxLayout()
        cur.setSpacing(10)

        self._cur_label = QLabel("Current file:")
        self._cur_label.setStyleSheet("font-size: 12px; color: #94a3b8; min-width: 90px;")

        self._cur_name = QLabel("—")
        self._cur_name.setStyleSheet("font-size: 12px; color: #e2e8f0;")
        self._cur_name.setMaximumWidth(300)

        self._cur_bar = QProgressBar()
        self._cur_bar.setRange(0, 100)
        self._cur_bar.setValue(0)
        self._cur_bar.setTextVisible(False)
        self._cur_bar.setFixedHeight(8)

        self._cur_pct = QLabel("0%")
        self._cur_pct.setMinimumWidth(40)
        self._cur_pct.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._cur_pct.setStyleSheet("color: #6c63ff; font-size: 12px; font-weight: 600;")

        cur.addWidget(self._cur_label)
        cur.addWidget(self._cur_name)
        cur.addWidget(self._cur_bar, stretch=1)
        cur.addWidget(self._cur_pct)
        layout.addLayout(cur)

        # ── Log header ──
        log_header = QHBoxLayout()
        log_title = QLabel("FFmpeg Log")
        log_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #94a3b8;")

        self._toggle_log_btn = QPushButton("▼  Hide")
        self._toggle_log_btn.setObjectName("secondary")
        self._toggle_log_btn.setFixedHeight(24)
        self._toggle_log_btn.setMaximumWidth(80)
        self._toggle_log_btn.clicked.connect(self._toggle_log)

        self._save_log_btn = QPushButton("💾  Save Log")
        self._save_log_btn.setObjectName("secondary")
        self._save_log_btn.setFixedHeight(24)
        self._save_log_btn.setMaximumWidth(100)
        self._save_log_btn.clicked.connect(self._save_log)

        self._clear_log_btn = QPushButton("Clear")
        self._clear_log_btn.setObjectName("secondary")
        self._clear_log_btn.setFixedHeight(24)
        self._clear_log_btn.setMaximumWidth(70)

        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(self._toggle_log_btn)
        log_header.addWidget(self._save_log_btn)
        log_header.addWidget(self._clear_log_btn)
        layout.addLayout(log_header)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(160)
        self._log.setPlaceholderText("FFmpeg output will appear here…")
        layout.addWidget(self._log)

        # Wire buttons after _log is created
        self._clear_log_btn.clicked.connect(self._log.clear)

        # ── Saved summary label ──
        self._saved_label = QLabel("")
        self._saved_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._saved_label.setStyleSheet("font-size: 12px; color: #22c55e; font-weight: 600;")
        layout.addWidget(self._saved_label)

    # ── Public API ────────────────────────────────────────────────────────────

    def reset(self):
        self._overall_bar.setValue(0)
        self._overall_pct.setText("0%")
        self._cur_bar.setValue(0)
        self._cur_pct.setText("0%")
        self._cur_name.setText("—")
        self._eta_label.setText("ETA: —")
        self._saved_label.setText("")
        self._log.clear()
        self._eta.start()

    def set_overall_progress(self, pct: float):
        v = int(min(100, max(0, pct)))
        self._overall_bar.setValue(v)
        self._overall_pct.setText(f"{v}%")
        self._eta_label.setText(f"ETA: {self._eta.get_eta(pct)}")

    def set_current_file(self, name: str):
        if len(name) > 40:
            name = "…" + name[-37:]
        self._cur_name.setText(name)
        self._cur_bar.setValue(0)
        self._cur_pct.setText("0%")

    def set_current_progress(self, pct: float):
        v = int(min(100, max(0, pct)))
        self._cur_bar.setValue(v)
        self._cur_pct.setText(f"{v}%")

    def append_log(self, line: str):
        """Append a line to the log. Colour-code errors/warnings."""
        line = line.strip()
        if not line:
            return
        if any(k in line.lower() for k in ("error", "invalid", "failed", "no such")):
            colour = "#ef4444"
        elif any(k in line.lower() for k in ("warning", "deprecated")):
            colour = "#f59e0b"
        elif line.startswith("▶") or line.startswith("─"):
            colour = "#6c63ff"
        elif line.startswith("frame=") or "time=" in line:
            colour = "#94a3b8"
        else:
            colour = "#64748b"
        self._log.append(
            f'<span style="color:{colour}; font-family:\'Cascadia Code\',monospace;">'
            f'{line}</span>'
        )
        # Auto-scroll
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_batch_summary(self, done: int, errors: int, saved_bytes: int):
        parts = [f"✅ {done} done"]
        if errors:
            parts.append(f"❌ {errors} errors")
        if saved_bytes > 0:
            parts.append(f"💾 Saved {format_size(saved_bytes)}")
        self._saved_label.setText("  •  ".join(parts))

    def set_idle(self):
        self._cur_name.setText("—")
        self._eta_label.setText("ETA: —")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _toggle_log(self):
        """Collapse or expand the log text area."""
        self._log_collapsed = not self._log_collapsed
        self._log.setVisible(not self._log_collapsed)
        self._toggle_log_btn.setText("▶  Show" if self._log_collapsed else "▼  Hide")

    def _save_log(self):
        """Export the current log content to a .txt file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save FFmpeg Log",
            os.path.join(os.path.expanduser("~"), "videoforge_log.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        if path:
            try:
                # QTextEdit.toPlainText() strips HTML tags
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._log.toPlainText())
            except Exception as e:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Save Failed", str(e))
