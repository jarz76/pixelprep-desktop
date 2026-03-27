"""Sidebar settings panel for PixelPrep desktop app."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class Dropdown(QComboBox):
    """ComboBox with a visible dropdown arrow indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._arrow_label = QLabel("▼", self)
        self._arrow_label.setStyleSheet("color: #8899AA; font-size: 9px; background: transparent;")
        self._arrow_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arrow_label.mousePressEvent = lambda e: self.showPopup()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position arrow on the right side
        self._arrow_label.move(self.width() - 20, (self.height() - 12) // 2)
        self._arrow_label.raise_()


class Sidebar(QWidget):
    """Left sidebar with output settings and export controls."""

    export_clicked = pyqtSignal()
    export_zip_clicked = pyqtSignal()
    add_files_clicked = pyqtSignal()
    add_folder_clicked = pyqtSignal()
    clear_all_clicked = pyqtSignal()
    settings_changed = pyqtSignal()
    preview_size_changed = pyqtSignal(int)  # card width in pixels

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(6)

        # --- App Title ---
        title = QLabel("PixelPrep")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #00BCD4; margin-bottom: 4px;")
        layout.addWidget(title)

        subtitle = QLabel("Bulk Resize & Crop")
        subtitle.setStyleSheet("color: #8899AA; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # --- Preview Size ---
        preview_row = QHBoxLayout()
        preview_label = QLabel("Preview Size")
        preview_label.setStyleSheet("color: #99AABB; font-size: 11px; font-weight: 600;")
        preview_row.addWidget(preview_label)
        self.preview_size_combo = Dropdown()
        self.preview_size_combo.addItem("Compact", 180)
        self.preview_size_combo.addItem("Default", 240)
        self.preview_size_combo.addItem("Large", 320)
        self.preview_size_combo.addItem("Extra Large", 400)
        self.preview_size_combo.setCurrentIndex(1)  # Default
        self.preview_size_combo.setStyleSheet(self._combo_small_style())
        self.preview_size_combo.currentIndexChanged.connect(self._on_preview_size_changed)
        preview_row.addWidget(self.preview_size_combo)
        layout.addLayout(preview_row)

        # --- Separator ---
        layout.addWidget(self._separator())

        # --- Output Mode ---
        layout.addWidget(self._label("Output Mode"))
        self.mode_combo = Dropdown()
        self.mode_combo.addItem("Fixed Size", "fixed_size")
        self.mode_combo.addItem("Fixed Aspect Ratio", "fixed_aspect_ratio")
        self.mode_combo.setStyleSheet(self._combo_style())
        self.mode_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        layout.addWidget(self.mode_combo)

        mode_hint = QLabel(
            "Fixed Size: exact output dimensions.\n"
            "Aspect Ratio: preserves max resolution."
        )
        mode_hint.setStyleSheet("color: #667788; font-size: 10px; margin-bottom: 4px;")
        mode_hint.setWordWrap(True)
        layout.addWidget(mode_hint)

        # --- Dimensions ---
        layout.addWidget(self._label("Width"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 16384)
        self.width_spin.setValue(512)
        self.width_spin.setSuffix(" px")
        self.width_spin.setStyleSheet(self._spin_style())
        self.width_spin.valueChanged.connect(lambda: self.settings_changed.emit())
        layout.addWidget(self.width_spin)

        layout.addWidget(self._label("Height"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 16384)
        self.height_spin.setValue(512)
        self.height_spin.setSuffix(" px")
        self.height_spin.setStyleSheet(self._spin_style())
        self.height_spin.valueChanged.connect(lambda: self.settings_changed.emit())
        layout.addWidget(self.height_spin)

        # --- Format ---
        layout.addWidget(self._separator())
        layout.addWidget(self._label("Format"))
        self.format_combo = Dropdown()
        self.format_combo.addItem("PNG", "png")
        self.format_combo.addItem("JPEG", "jpeg")
        self.format_combo.setStyleSheet(self._combo_style())
        self.format_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        layout.addWidget(self.format_combo)

        # --- Zip filename template ---
        layout.addWidget(self._label("Zip Filename"))
        self.zip_name_edit = QLineEdit()
        self.zip_name_edit.setPlaceholderText("PixelPrep_{timestamp}")
        self.zip_name_edit.setText("PixelPrep_{timestamp}")
        self.zip_name_edit.setStyleSheet(self._input_style())
        layout.addWidget(self.zip_name_edit)

        # --- Image count ---
        layout.addWidget(self._separator())
        self.count_label = QLabel("0 images loaded")
        self.count_label.setStyleSheet("color: #8899AA; font-size: 12px; padding: 4px 0;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # --- Buttons ---
        self.add_btn = QPushButton("＋  Add Files")
        self.add_btn.setStyleSheet(self._btn_secondary_style())
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_files_clicked.emit)
        layout.addWidget(self.add_btn)

        self.add_folder_btn = QPushButton("📁  Add Folder")
        self.add_folder_btn.setStyleSheet(self._btn_secondary_style())
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.clicked.connect(self.add_folder_clicked.emit)
        layout.addWidget(self.add_folder_btn)

        self.clear_btn = QPushButton("🗑️  Clear All")
        self.clear_btn.setStyleSheet(self._btn_clear_style())
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_all_clicked.emit)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)

        self.export_folder_btn = QPushButton("📂  Export to Folder")
        self.export_folder_btn.setStyleSheet(self._btn_primary_style())
        self.export_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_folder_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self.export_folder_btn)

        self.export_zip_btn = QPushButton("📦  Save as ZIP")
        self.export_zip_btn.setStyleSheet(self._btn_primary_style())
        self.export_zip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_zip_btn.clicked.connect(self.export_zip_clicked.emit)
        layout.addWidget(self.export_zip_btn)

        # --- Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m")
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background: #1E2A35;
                height: 22px;
                text-align: center;
                color: #CCDDEE;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4, stop:1 #0097A7);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

    # ── Properties ──────────────────────────────────────────

    @property
    def output_mode(self) -> str:
        return self.mode_combo.currentData()

    @property
    def output_width(self) -> int:
        return self.width_spin.value()

    @property
    def output_height(self) -> int:
        return self.height_spin.value()

    @property
    def output_format(self) -> str:
        return self.format_combo.currentData()

    @property
    def zip_filename_template(self) -> str:
        return self.zip_name_edit.text().strip() or "PixelPrep_{timestamp}"

    @property
    def preview_size(self) -> int:
        return self.preview_size_combo.currentData()

    def _on_preview_size_changed(self):
        self.preview_size_changed.emit(self.preview_size)

    def set_image_count(self, count: int):
        self.count_label.setText(f"{count} image{'s' if count != 1 else ''} loaded")
        self.clear_btn.setVisible(count > 0)

    def set_exporting(self, exporting: bool, total: int = 0):
        self.export_folder_btn.setEnabled(not exporting)
        self.export_zip_btn.setEnabled(not exporting)
        self.add_btn.setEnabled(not exporting)
        self.add_folder_btn.setEnabled(not exporting)
        self.progress_bar.setVisible(exporting)
        if exporting:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(0)

    def update_progress(self, completed: int, total: int):
        self.progress_bar.setValue(completed)

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #99AABB; font-size: 11px; font-weight: 600; margin-top: 8px;")
        return lbl

    @staticmethod
    def _separator() -> QWidget:
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #2A3A4A; margin: 8px 0;")
        return sep

    @staticmethod
    def _combo_style() -> str:
        return """
            QComboBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 28px 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QComboBox:hover { border-color: #00BCD4; }
            QComboBox::drop-down { width: 0; border: none; }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                color: #D0DEE8;
                selection-background-color: #00BCD4;
                selection-color: #FFFFFF;
                padding: 4px;
            }
        """

    @staticmethod
    def _combo_small_style() -> str:
        return """
            QComboBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                padding: 4px 22px 4px 8px;
                color: #D0DEE8;
                font-size: 11px;
            }
            QComboBox:hover { border-color: #00BCD4; }
            QComboBox::drop-down { width: 0; border: none; }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                color: #D0DEE8;
                selection-background-color: #00BCD4;
                selection-color: #FFFFFF;
                padding: 2px;
            }
        """

    @staticmethod
    def _spin_style() -> str:
        return """
            QSpinBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QSpinBox:hover { border-color: #00BCD4; }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background: transparent;
            }
        """

    @staticmethod
    def _input_style() -> str:
        return """
            QLineEdit {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QLineEdit:hover { border-color: #00BCD4; }
            QLineEdit:focus { border-color: #00BCD4; }
        """

    @staticmethod
    def _btn_primary_style() -> str:
        return """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4, stop:1 #0097A7);
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #26C6DA, stop:1 #00ACC1);
            }
            QPushButton:pressed { background: #00838F; }
            QPushButton:disabled { background: #2A3A4A; color: #556677; }
        """

    @staticmethod
    def _btn_secondary_style() -> str:
        return """
            QPushButton {
                background: transparent;
                border: 1px solid #2A3A4A;
                border-radius: 8px;
                padding: 10px 16px;
                color: #8899AA;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }
            QPushButton:pressed { background: #1A2530; }
        """

    @staticmethod
    def _btn_clear_style() -> str:
        return """
            QPushButton {
                background: transparent;
                border: 1px solid #3A2A2A;
                border-radius: 8px;
                padding: 8px 16px;
                color: #AA6666;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { border-color: #FF5555; color: #FF5555; background: #2A1515; }
            QPushButton:pressed { background: #1A1010; }
        """
