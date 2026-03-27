"""PixelPrep Desktop — Entry Point.

A high-performance native desktop app for bulk image resizing and cropping.
"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


def apply_dark_theme(app: QApplication):
    """Apply a sleek dark theme using Qt Fusion style + custom palette."""
    app.setStyle("Fusion")

    palette = QPalette()

    # Base colors
    bg_dark = QColor("#0F1923")
    bg_mid = QColor("#151E28")
    bg_light = QColor("#1E2A35")
    text_primary = QColor("#D0DEE8")
    text_secondary = QColor("#8899AA")
    accent = QColor("#00BCD4")
    border = QColor("#2A3A4A")

    palette.setColor(QPalette.ColorRole.Window, bg_mid)
    palette.setColor(QPalette.ColorRole.WindowText, text_primary)
    palette.setColor(QPalette.ColorRole.Base, bg_dark)
    palette.setColor(QPalette.ColorRole.AlternateBase, bg_light)
    palette.setColor(QPalette.ColorRole.ToolTipBase, bg_light)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
    palette.setColor(QPalette.ColorRole.Text, text_primary)
    palette.setColor(QPalette.ColorRole.Button, bg_light)
    palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, text_secondary)

    # Disabled state
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#556677"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#556677"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#556677"))

    app.setPalette(palette)

    # Global stylesheet for scrollbars, tooltips, and general polish
    app.setStyleSheet("""
        QToolTip {
            background: #1E2A35;
            color: #D0DEE8;
            border: 1px solid #2A3A4A;
            padding: 6px;
            border-radius: 4px;
            font-size: 12px;
        }
        QScrollBar:vertical {
            background: #0F1923;
            width: 10px;
            border: none;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #2A3A4A;
            min-height: 30px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #3A4A5A;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background: #0F1923;
            height: 10px;
            border: none;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal {
            background: #2A3A4A;
            min-width: 30px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #3A4A5A;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        QMessageBox {
            background: #151E28;
        }
        QMessageBox QLabel {
            color: #D0DEE8;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background: #1E2A35;
            border: 1px solid #2A3A4A;
            border-radius: 6px;
            padding: 6px 20px;
            color: #D0DEE8;
            font-size: 12px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            border-color: #00BCD4;
            color: #00BCD4;
        }
    """)


def main():
    app = QApplication(sys.argv)

    # Set default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    apply_dark_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
