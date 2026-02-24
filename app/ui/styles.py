"""
styles.py — Dark mode QSS stylesheet for VideoForge Pro
"""

APP_STYLESHEET = """
/* ═══════════════════════════════════════════════════════
   VideoForge Pro — Dark Mode Stylesheet
   Palette:
     bg-dark:   #0f1117
     bg-mid:    #1a1d27
     bg-card:   #21263a
     accent:    #6c63ff
     accent2:   #a78bfa
     success:   #22c55e
     warning:   #f59e0b
     danger:    #ef4444
     text:      #e2e8f0
     text-dim:  #94a3b8
   ═══════════════════════════════════════════════════════ */

QMainWindow, QDialog {
    background-color: #0f1117;
}

QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #21263a;
    width: 2px;
    height: 2px;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #1a1d27;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #6c63ff;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1a1d27;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #6c63ff;
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Group Boxes ── */
QGroupBox {
    background-color: #1a1d27;
    border: 1px solid #2d3348;
    border-radius: 10px;
    margin-top: 16px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    color: #a78bfa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -2px;
    padding: 0 6px;
    background-color: #1a1d27;
    color: #a78bfa;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Labels ── */
QLabel {
    background: transparent;
    color: #e2e8f0;
}
QLabel#dim {
    color: #94a3b8;
    font-size: 12px;
}
QLabel#title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#subtitle {
    font-size: 12px;
    color: #94a3b8;
}

/* ── Buttons ── */
QPushButton {
    background-color: #6c63ff;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #7c74ff;
}
QPushButton:pressed {
    background-color: #5a52e8;
}
QPushButton:disabled {
    background-color: #2d3348;
    color: #4b5563;
}
QPushButton#secondary {
    background-color: #21263a;
    color: #a78bfa;
    border: 1px solid #6c63ff;
}
QPushButton#secondary:hover {
    background-color: #2d3356;
}
QPushButton#danger {
    background-color: #ef4444;
}
QPushButton#danger:hover {
    background-color: #dc2626;
}
QPushButton#success {
    background-color: #22c55e;
}
QPushButton#success:hover {
    background-color: #16a34a;
}
QPushButton#icon-btn {
    background-color: transparent;
    padding: 4px 8px;
    border: none;
    font-size: 16px;
}
QPushButton#icon-btn:hover {
    background-color: #21263a;
    border-radius: 6px;
}

/* ── Input Fields ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QTimeEdit {
    background-color: #21263a;
    border: 1px solid #2d3348;
    border-radius: 7px;
    padding: 6px 10px;
    color: #e2e8f0;
    selection-background-color: #6c63ff;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus {
    border: 1px solid #6c63ff;
}
QLineEdit:disabled, QSpinBox:disabled {
    color: #4b5563;
    background-color: #1a1d27;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: transparent;
    width: 14px;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #21263a;
    border: 1px solid #2d3348;
    border-radius: 7px;
    padding: 6px 10px;
    color: #e2e8f0;
    min-width: 100px;
}
QComboBox:hover {
    border: 1px solid #6c63ff;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #6c63ff;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background-color: #21263a;
    border: 1px solid #6c63ff;
    border-radius: 7px;
    selection-background-color: #6c63ff;
    selection-color: white;
    color: #e2e8f0;
    padding: 4px;
}

/* ── Checkboxes ── */
QCheckBox {
    spacing: 8px;
    color: #e2e8f0;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 2px solid #2d3348;
    background-color: #21263a;
}
QCheckBox::indicator:checked {
    background-color: #6c63ff;
    border-color: #6c63ff;
    image: none;
}
QCheckBox::indicator:hover {
    border-color: #6c63ff;
}

/* ── Sliders ── */
QSlider::groove:horizontal {
    height: 6px;
    background: #2d3348;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #6c63ff;
    border: none;
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px 0;
}
QSlider::handle:horizontal:hover {
    background: #7c74ff;
    width: 20px;
    height: 20px;
    border-radius: 10px;
    margin: -7px 0;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6c63ff, stop:1 #a78bfa);
    border-radius: 3px;
}

/* ── Progress Bar ── */
QProgressBar {
    background-color: #21263a;
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6c63ff, stop:1 #a78bfa);
    border-radius: 6px;
}

/* ── Tab Widget ── */
QTabWidget::pane {
    background-color: #1a1d27;
    border: 1px solid #2d3348;
    border-radius: 10px;
    padding: 10px;
}
QTabBar::tab {
    background-color: #21263a;
    color: #94a3b8;
    border-radius: 7px;
    padding: 8px 16px;
    margin: 2px 2px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #6c63ff;
    color: white;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background-color: #2d3348;
    color: #e2e8f0;
}

/* ── List Widget ── */
QListWidget {
    background-color: #1a1d27;
    border: 1px solid #2d3348;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}
QListWidget::item {
    background-color: #21263a;
    border-radius: 7px;
    padding: 8px 10px;
    margin: 2px 0;
    color: #e2e8f0;
}
QListWidget::item:selected {
    background-color: #2d3356;
    color: #a78bfa;
}
QListWidget::item:hover:!selected {
    background-color: #252840;
}

/* ── Text Edit (Log) ── */
QTextEdit, QPlainTextEdit {
    background-color: #0d1020;
    border: 1px solid #2d3348;
    border-radius: 8px;
    color: #94a3b8;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #1a1d27;
    border-bottom: 1px solid #2d3348;
    padding: 6px 8px;
    spacing: 6px;
}
QToolBar::separator {
    background-color: #2d3348;
    width: 1px;
    margin: 4px 6px;
}

/* ── Status Bar ── */
QStatusBar {
    background-color: #1a1d27;
    border-top: 1px solid #2d3348;
    color: #94a3b8;
    font-size: 12px;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #21263a;
    color: #e2e8f0;
    border: 1px solid #6c63ff;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── Separator ── */
QFrame[frameShape="4"], QFrame[frameShape="HLine"] {
    color: #2d3348;
    background-color: #2d3348;
    max-height: 1px;
}

/* ── Menu ── */
QMenuBar {
    background-color: #1a1d27;
    color: #e2e8f0;
    border-bottom: 1px solid #2d3348;
}
QMenuBar::item:selected {
    background-color: #6c63ff;
    border-radius: 5px;
}
QMenu {
    background-color: #21263a;
    border: 1px solid #6c63ff;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 16px;
    border-radius: 5px;
}
QMenu::item:selected {
    background-color: #6c63ff;
}
"""

# Accent gradient for special buttons
GRADIENT_ACCENT = "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #a78bfa);"

COLORS = {
    "bg_dark":   "#0f1117",
    "bg_mid":    "#1a1d27",
    "bg_card":   "#21263a",
    "accent":    "#6c63ff",
    "accent2":   "#a78bfa",
    "success":   "#22c55e",
    "warning":   "#f59e0b",
    "danger":    "#ef4444",
    "text":      "#e2e8f0",
    "text_dim":  "#94a3b8",
}
