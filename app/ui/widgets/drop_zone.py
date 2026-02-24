"""
drop_zone.py — Drag & drop file acceptance widget for VideoForge Pro
"""
import os
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


SUPPORTED_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".gif",
                  ".m4v", ".flv", ".wmv", ".ts", ".3gp", ".mpg", ".mpeg"}


class DropZone(QWidget):
    """
    A stylised drag-and-drop target that accepts video files.
    Emits files_dropped(list[str]) when files are dropped.
    Emits browse_clicked() when the inner label is clicked.
    """

    files_dropped = pyqtSignal(list)
    browse_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        self._hover = False
        self._drag_over = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        self._icon = QLabel("🎬")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(36)
        self._icon.setFont(icon_font)
        self._icon.setStyleSheet("background: transparent;")

        self._main_label = QLabel("Drop videos here")
        self._main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_label.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #e2e8f0; background: transparent;"
        )

        self._sub_label = QLabel("or click to browse  •  MP4, MKV, MOV, AVI, WEBM, GIF")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_label.setStyleSheet(
            "font-size: 12px; color: #94a3b8; background: transparent;"
        )

        for w in (self._icon, self._main_label, self._sub_label):
            layout.addWidget(w)

        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._drag_over:
            bg = QColor("#1e1b4b")
            border_color = QColor("#a78bfa")
            dash = Qt.PenStyle.SolidLine
        elif self._hover:
            bg = QColor("#1a1d27")
            border_color = QColor("#6c63ff")
            dash = Qt.PenStyle.DashLine
        else:
            bg = QColor("#1a1d27")
            border_color = QColor("#2d3348")
            dash = Qt.PenStyle.DashLine

        painter.setBrush(bg)
        pen = QPen(border_color, 2, dash)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)

    # ── Events ────────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.browse_clicked.emit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if any(os.path.splitext(p)[1].lower() in SUPPORTED_EXTS for p in paths):
                event.acceptProposedAction()
                self._drag_over = True
                self._main_label.setText("Release to add files ✨")
                self.update()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self._main_label.setText("Drop videos here")
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._drag_over = False
        self._main_label.setText("Drop videos here")
        self.update()
        paths = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if os.path.isfile(local) and os.path.splitext(local)[1].lower() in SUPPORTED_EXTS:
                paths.append(local)
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def set_dragging(self, active: bool):
        """Called externally to force drag-over appearance."""
        self._drag_over = active
        self.update()
