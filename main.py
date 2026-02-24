"""
main.py — Entry point for VideoForge Pro
"""
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoForge Pro")
    app.setApplicationDisplayName("VideoForge Pro")
    app.setOrganizationName("VideoForge")
    app.setApplicationVersion("1.0.0")

    # Apply global dark stylesheet
    app.setStyleSheet(APP_STYLESHEET)

    # Modern font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
