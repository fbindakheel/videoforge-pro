"""
file_list.py — Batch file list panel with per-file status indicators for VideoForge Pro
"""
import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QSizePolicy,
)
from app.core.utils import format_size
from app.core.batch_processor import JobStatus


STATUS_ICONS = {
    JobStatus.PENDING:   ("⏳", "#94a3b8"),
    JobStatus.RUNNING:   ("⚡", "#f59e0b"),
    JobStatus.DONE:      ("✅", "#22c55e"),
    JobStatus.ERROR:     ("❌", "#ef4444"),
    JobStatus.CANCELLED: ("⛔", "#6b7280"),
}


class FileItemWidget(QWidget):
    """Widget displayed inside each QListWidgetItem row."""

    remove_clicked = pyqtSignal(int)  # row index

    def __init__(self, index: int, path: str, size: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._path = path
        self._size = size
        self._status = JobStatus.PENDING
        self._output_size = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._status_icon = QLabel("⏳")
        self._status_icon.setFixedWidth(22)
        self._status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_icon.setStyleSheet("font-size: 14px; background: transparent;")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self._name_label = QLabel(os.path.basename(self._path))
        self._name_label.setStyleSheet(
            "font-weight: 600; font-size: 13px; color: #e2e8f0; background: transparent;"
        )
        self._name_label.setToolTip(self._path)

        self._info_label = QLabel(f"{format_size(self._size)}  •  {self._path}")
        self._info_label.setStyleSheet(
            "font-size: 11px; color: #94a3b8; background: transparent;"
        )
        self._info_label.setToolTip(self._path)

        info_layout.addWidget(self._name_label)
        info_layout.addWidget(self._info_label)

        self._remove_btn = QPushButton("✕")
        self._remove_btn.setFixedSize(24, 24)
        self._remove_btn.setObjectName("icon-btn")
        self._remove_btn.setToolTip("Remove from list")
        self._remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.index))

        layout.addWidget(self._status_icon)
        layout.addLayout(info_layout, stretch=1)
        layout.addWidget(self._remove_btn)

    def set_status(self, status: JobStatus, progress: float = 0.0, error: str = ""):
        self._status = status
        icon_char, color = STATUS_ICONS.get(status, ("❓", "#e2e8f0"))
        self._status_icon.setText(icon_char)
        self._status_icon.setStyleSheet(
            f"font-size: 14px; color: {color}; background: transparent;"
        )
        if status == JobStatus.RUNNING:
            pct = int(progress)
            self._info_label.setText(
                f"{format_size(self._size)}  •  Processing… {pct}%"
            )
            self._info_label.setStyleSheet(
                f"font-size: 11px; color: {color}; background: transparent;"
            )
        elif status == JobStatus.DONE and self._output_size > 0:
            saved = self._size - self._output_size
            ratio = (1 - self._output_size / self._size) * 100 if self._size else 0
            self._info_label.setText(
                f"{format_size(self._size)} → {format_size(self._output_size)}"
                f"  •  Saved {format_size(saved)} ({ratio:.0f}%)"
            )
            self._info_label.setStyleSheet(
                f"font-size: 11px; color: {color}; background: transparent;"
            )
        elif status == JobStatus.ERROR:
            self._info_label.setText(f"Error: {error}")
            self._info_label.setStyleSheet(
                "font-size: 11px; color: #ef4444; background: transparent;"
            )

    def set_output_size(self, size: int):
        self._output_size = size

    @property
    def status(self) -> JobStatus:
        return self._status


class FileListPanel(QWidget):
    """
    The batch file list widget. Shows all queued files with status icons
    and allows individual removal.
    """

    files_removed = pyqtSignal(int)      # emits the row index removed
    file_selected = pyqtSignal(str)      # emits the file path when clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_widgets: list[FileItemWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        title = QLabel("Queue")
        title.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #e2e8f0;"
        )
        self._count_badge = QLabel("0 files")
        self._count_badge.setStyleSheet(
            "font-size: 11px; color: #6c63ff; font-weight: 600; "
            "background: #1e1b4b; border-radius: 8px; padding: 2px 8px;"
        )

        # Clear Done button
        self._clear_done_btn = QPushButton("✅ Clear Done")
        self._clear_done_btn.setObjectName("secondary")
        self._clear_done_btn.setFixedHeight(26)
        self._clear_done_btn.setToolTip("Remove all completed files from the queue")
        self._clear_done_btn.clicked.connect(self._clear_done)
        self._clear_done_btn.setVisible(False)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._clear_done_btn)
        header.addSpacing(6)
        header.addWidget(self._count_badge)

        layout.addLayout(header)
        layout.addSpacing(8)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self._list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list)

        self._empty_label = QLabel("No files added yet")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #94a3b8; font-size: 13px; padding: 20px;"
        )
        layout.addWidget(self._empty_label)
        self._empty_label.setVisible(True)

    def add_file(self, path: str, size: int) -> int:
        """Add a file row. Returns its row index."""
        index = len(self._file_widgets)
        item_widget = FileItemWidget(index, path, size)
        item_widget.remove_clicked.connect(self._on_remove)

        item = QListWidgetItem(self._list)
        item.setSizeHint(item_widget.sizeHint())
        self._list.addItem(item)
        self._list.setItemWidget(item, item_widget)
        self._file_widgets.append(item_widget)
        self._refresh_visibility()
        return index

    def _on_remove(self, index: int):
        if 0 <= index < self._list.count():
            item = self._list.takeItem(index)
            del item
            # Re-index remaining widgets
            self._file_widgets.pop(index)
            for i, w in enumerate(self._file_widgets):
                w.index = i
            self._refresh_visibility()
            self.files_removed.emit(index)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Emit file_selected with the path of the clicked item."""
        row = self._list.row(item)
        if 0 <= row < len(self._file_widgets):
            self.file_selected.emit(self._file_widgets[row]._path)

    def _clear_done(self):
        """Remove all items with DONE status from the queue."""
        indices_to_remove = [
            i for i, w in enumerate(self._file_widgets)
            if w.status == JobStatus.DONE
        ]
        # Remove in reverse order to keep indices valid
        for i in reversed(indices_to_remove):
            item = self._list.takeItem(i)
            del item
            self._file_widgets.pop(i)
        # Re-index remaining
        for i, w in enumerate(self._file_widgets):
            w.index = i
        self._refresh_visibility()

    def update_job_status(self, index: int, status: JobStatus,
                          progress: float = 0.0, error: str = "",
                          output_size: int = 0):
        if 0 <= index < len(self._file_widgets):
            w = self._file_widgets[index]
            if output_size:
                w.set_output_size(output_size)
            w.set_status(status, progress, error)
        # Show "Clear Done" button if any items are done
        has_done = any(w.status == JobStatus.DONE for w in self._file_widgets)
        self._clear_done_btn.setVisible(has_done)

    def clear_all(self):
        self._list.clear()
        self._file_widgets.clear()
        self._refresh_visibility()

    def _refresh_visibility(self):
        count = self._list.count()
        self._empty_label.setVisible(count == 0)
        self._list.setVisible(count > 0)
        self._count_badge.setText(f"{count} file{'s' if count != 1 else ''}")
        # Hide clear done if nothing is done
        has_done = any(w.status == JobStatus.DONE for w in self._file_widgets)
        self._clear_done_btn.setVisible(has_done)

    def file_paths(self) -> list[str]:
        return [w._path for w in self._file_widgets]

    def count(self) -> int:
        return self._list.count()
