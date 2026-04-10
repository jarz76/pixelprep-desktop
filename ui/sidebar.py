"""Sidebar settings panel for PixelPrep desktop app."""

from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
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
    caption_all_clicked = pyqtSignal()
    caption_missing_clicked = pyqtSignal()
    caption_settings_changed = pyqtSignal()
    replace_all_clicked = pyqtSignal(str, str)

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

        layout.addWidget(self._separator())

        # --- TABS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2A3A4A; border-radius: 4px; background: #1E2A35; }
            QTabBar::tab { background: #151E28; color: #8899AA; padding: 6px 12px; border: 1px solid #2A3A4A; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1E2A35; color: #00BCD4; }
        """)
        layout.addWidget(self.tabs)

        # TAB 1: Export Options
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(10, 10, 10, 10)
        export_layout.setSpacing(6)

        export_layout.addWidget(self._label("Output Mode"))
        self.mode_combo = Dropdown()
        self.mode_combo.addItem("Fixed Size", "fixed_size")
        self.mode_combo.addItem("Fixed Aspect Ratio", "fixed_aspect_ratio")
        self.mode_combo.setStyleSheet(self._combo_style())
        self.mode_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        export_layout.addWidget(self.mode_combo)

        mode_hint = QLabel("Fixed Size: exact output dimensions.\nAspect Ratio: preserves max resolution.")
        mode_hint.setStyleSheet("color: #667788; font-size: 10px; margin-bottom: 4px;")
        mode_hint.setWordWrap(True)
        export_layout.addWidget(mode_hint)

        dim_layout = QHBoxLayout()
        dim_layout.setSpacing(10)

        w_layout = QVBoxLayout()
        w_layout.setSpacing(2)
        w_layout.addWidget(self._label("Width"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 16384)
        self.width_spin.setValue(512)
        self.width_spin.setSuffix(" px")
        self.width_spin.setStyleSheet(self._spin_style())
        self.width_spin.valueChanged.connect(lambda: self.settings_changed.emit())
        w_layout.addWidget(self.width_spin)
        dim_layout.addLayout(w_layout)

        h_layout = QVBoxLayout()
        h_layout.setSpacing(2)
        h_layout.addWidget(self._label("Height"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 16384)
        self.height_spin.setValue(512)
        self.height_spin.setSuffix(" px")
        self.height_spin.setStyleSheet(self._spin_style())
        self.height_spin.valueChanged.connect(lambda: self.settings_changed.emit())
        h_layout.addWidget(self.height_spin)
        dim_layout.addLayout(h_layout)

        export_layout.addLayout(dim_layout)

        export_layout.addWidget(self._separator())
        export_layout.addWidget(self._label("Export Type"))
        self.export_type_combo = Dropdown()
        self.export_type_combo.addItem("Image + Caption", "both")
        self.export_type_combo.addItem("Image Only", "image")
        self.export_type_combo.addItem("Caption Only", "caption")
        self.export_type_combo.setStyleSheet(self._combo_style())
        self.export_type_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        export_layout.addWidget(self.export_type_combo)

        export_layout.addWidget(self._label("Image Format"))
        self.format_combo = Dropdown()
        self.format_combo.addItem("PNG", "png")
        self.format_combo.addItem("JPEG", "jpeg")
        self.format_combo.setStyleSheet(self._combo_style())
        self.format_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        export_layout.addWidget(self.format_combo)

        export_layout.addWidget(self._label("Zip Filename"))
        self.zip_name_edit = QLineEdit()
        self.zip_name_edit.setPlaceholderText("PixelPrep_{timestamp}")
        self.zip_name_edit.setText("PixelPrep_{timestamp}")
        self.zip_name_edit.setStyleSheet(self._input_style())
        export_layout.addWidget(self.zip_name_edit)
        export_layout.addStretch()

        self.tabs.addTab(export_tab, "Export")

        # TAB 2: Caption
        caption_tab = QWidget()
        caption_layout = QVBoxLayout(caption_tab)
        caption_layout.setContentsMargins(10, 10, 10, 10)
        caption_layout.setSpacing(6)

        settings = QSettings("PixelPrep", "Settings")

        # API Settings button row
        api_row = QHBoxLayout()
        api_row.setSpacing(6)

        self._api_info_label = QLabel()
        self._update_api_info_label()
        self._api_info_label.setTextFormat(Qt.TextFormat.RichText)
        self._api_info_label.setStyleSheet("background: transparent;")
        api_row.addWidget(self._api_info_label, 1)

        api_cfg_btn = QPushButton("⚙ API Settings")
        api_cfg_btn.setStyleSheet(self._btn_secondary_style() + "QPushButton { padding: 4px 8px; font-size: 11px; }")
        api_cfg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        api_cfg_btn.clicked.connect(self._open_api_settings)
        api_row.addWidget(api_cfg_btn)
        caption_layout.addLayout(api_row)

        caption_layout.addWidget(self._separator_thin())

        # Model
        caption_layout.addWidget(self._label("Model"))
        model_row = QHBoxLayout()
        model_row.setSpacing(4)
        
        self.api_model_combo = QComboBox()
        self.api_model_combo.setEditable(True)
        self.api_model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.api_model_combo.setStyleSheet(self._combo_editable_style())
        
        # Make the dropdown searchable
        completer = self.api_model_combo.completer()
        if completer is not None:
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCompletionMode(completer.CompletionMode.PopupCompletion)

        saved_model = settings.value("api_model", "gpt-4o")
        self.api_model_combo.setCurrentText(saved_model)
        self.api_model_combo.currentTextChanged.connect(self._save_caption_settings)
        model_row.addWidget(self.api_model_combo, 1)

        self.refresh_model_btn = QPushButton("↻")
        self.refresh_model_btn.setToolTip("Fetch models from Provider")
        self.refresh_model_btn.setFixedWidth(28)
        self.refresh_model_btn.setStyleSheet(self._btn_secondary_style() + "QPushButton { padding: 0; font-size: 14px; }")
        self.refresh_model_btn.clicked.connect(self._fetch_models)
        model_row.addWidget(self.refresh_model_btn)
        
        caption_layout.addLayout(model_row)

        self.vision_only_cb = QCheckBox("Show Vision models only")
        self.vision_only_cb.setChecked(settings.value("api_vision_only", True, type=bool))
        self.vision_only_cb.setStyleSheet("""
            QCheckBox { color: #8899AA; font-size: 11px; margin-left: 2px; }
            QCheckBox::indicator { width: 14px; height: 14px; border-radius: 3px; border: 1px solid #2A3A4A; background: #1E2A35; }
            QCheckBox::indicator:checked { background: #00BCD4; border: 1px solid #00BCD4; }
        """)
        self.vision_only_cb.stateChanged.connect(self._save_caption_settings)
        caption_layout.addWidget(self.vision_only_cb)

        caption_layout.addWidget(self._label("System Prompt"))
        self.api_prompt_edit = QTextEdit()
        self.api_prompt_edit.setPlaceholderText("e.g. Describe this image in detail, focusing on style, composition, and subject.")
        self.api_prompt_edit.setText(settings.value("api_prompt", "Describe this image in detail."))
        self.api_prompt_edit.setStyleSheet(self._textedit_style())
        self.api_prompt_edit.textChanged.connect(self._save_caption_settings)
        caption_layout.addWidget(self.api_prompt_edit, 1)  # stretch=1 -> expand

        self.cap_all_btn = QPushButton("✨ Caption All")
        self.cap_all_btn.setStyleSheet(self._btn_secondary_style())
        self.cap_all_btn.clicked.connect(self.caption_all_clicked.emit)
        caption_layout.addWidget(self.cap_all_btn)

        self.cap_missing_btn = QPushButton("✨ Caption Missing")
        self.cap_missing_btn.setStyleSheet(self._btn_secondary_style())
        self.cap_missing_btn.clicked.connect(self.caption_missing_clicked.emit)
        caption_layout.addWidget(self.cap_missing_btn)
        
        caption_layout.addStretch()
        self.tabs.addTab(caption_tab, "Caption")

        # TAB 3: Batch Edit
        edit_tab = QWidget()
        edit_layout = QVBoxLayout(edit_tab)
        edit_layout.setContentsMargins(10, 10, 10, 10)
        edit_layout.setSpacing(6)

        edit_layout.addWidget(self._label("Target Word/Phrase"))
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Text to find...")
        self.find_edit.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.find_edit)

        edit_layout.addWidget(self._label("Replace With"))
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("New text...")
        self.replace_edit.setStyleSheet(self._input_style())
        edit_layout.addWidget(self.replace_edit)

        self.replace_btn = QPushButton("✏️ Replace All")
        self.replace_btn.setStyleSheet(self._btn_secondary_style())
        self.replace_btn.clicked.connect(self._emit_replace_all)
        edit_layout.addWidget(self.replace_btn)

        edit_layout.addStretch()
        self.tabs.addTab(edit_tab, "Trigger Word")

        # --- Bottom area: counts & global actions ---
        layout.addWidget(self._separator())
        self.count_label = QLabel("0 images loaded")
        self.count_label.setStyleSheet("color: #8899AA; font-size: 12px; padding: 4px 0;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("＋ Add Files")
        self.add_btn.setStyleSheet(self._btn_secondary_style())
        self.add_btn.clicked.connect(self.add_files_clicked.emit)
        btn_row.addWidget(self.add_btn)

        self.add_folder_btn = QPushButton("📁 Add Folder")
        self.add_folder_btn.setStyleSheet(self._btn_secondary_style())
        self.add_folder_btn.clicked.connect(self.add_folder_clicked.emit)
        btn_row.addWidget(self.add_folder_btn)
        layout.addLayout(btn_row)

        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.setStyleSheet(self._btn_clear_style())
        self.clear_btn.clicked.connect(self.clear_all_clicked.emit)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)

        export_btn_row = QHBoxLayout()
        export_btn_row.setSpacing(6)

        self.export_folder_btn = QPushButton("📂 To Folder")
        self.export_folder_btn.setStyleSheet(self._btn_primary_style())
        self.export_folder_btn.clicked.connect(self.export_clicked.emit)
        export_btn_row.addWidget(self.export_folder_btn)

        self.export_zip_btn = QPushButton("📦 As ZIP")
        self.export_zip_btn.setStyleSheet(self._btn_primary_style())
        self.export_zip_btn.clicked.connect(self.export_zip_clicked.emit)
        export_btn_row.addWidget(self.export_zip_btn)

        layout.addLayout(export_btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m")
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 6px; background: #1E2A35; height: 22px; text-align: center; color: #CCDDEE; font-size: 11px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4, stop:1 #0097A7); border-radius: 6px; }
        """)
        layout.addWidget(self.progress_bar)

    def _save_caption_settings(self):
        settings = QSettings("PixelPrep", "Settings")
        settings.setValue("api_model", self.api_model_combo.currentText().strip())
        settings.setValue("api_prompt", self.api_prompt_edit.toPlainText())
        settings.setValue("api_vision_only", self.vision_only_cb.isChecked())

    def _update_api_info_label(self):
        settings = QSettings("PixelPrep", "Settings")
        url = settings.value("api_url", "https://api.openai.com")
        url_short = url.replace("https://", "").replace("http://", "").rstrip("/")
        if len(url_short) > 30: url_short = url_short[:30] + "…"
        self._api_info_label.setText(
            f"<span style='color:#8899AA;font-size:10px;'>{url_short}</span>"
        )

    def _emit_replace_all(self):
        target = self.find_edit.text()
        new_text = self.replace_edit.text()
        if target:
            self.replace_all_clicked.emit(target, new_text)

    def _open_api_settings(self):
        from ui.api_settings_dialog import ApiSettingsDialog
        dlg = ApiSettingsDialog(self)
        if dlg.exec():
            self._update_api_info_label()
            self.caption_settings_changed.emit()

    def _fetch_models(self):
        import json
        import urllib.request
        import ssl
        from PyQt6.QtWidgets import QMessageBox

        settings = QSettings("PixelPrep", "Settings")
        base_url = settings.value("api_url", "https://api.openai.com").strip().rstrip('/')
        api_key = settings.value("api_key", "").strip()

        if not base_url:
            QMessageBox.warning(self, "Error", "Please configure a Base URL in settings first.")
            return

        endpoint = f"{base_url}/v1/models"
        self.refresh_model_btn.setText("...")
        self.refresh_model_btn.setEnabled(False)
        self.api_model_combo.clear()

        vision_only = self.vision_only_cb.isChecked()

        def worker():
            try:
                headers = {"Accept": "application/json"}
                if api_key: headers["Authorization"] = f"Bearer {api_key}"
                req = urllib.request.Request(endpoint, headers=headers)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    
                models = []
                if "data" in data and isinstance(data["data"], list):
                    for m in data["data"]:
                        if vision_only and isinstance(m, dict) and "architecture" in m:
                            arch = m.get("architecture")
                            if isinstance(arch, dict):
                                mods = arch.get("input_modalities", [])
                                if isinstance(mods, list) and "image" not in mods:
                                    continue  # Skip because it explicitly lacks image input
                        models.append(m.get("id", m.get("model", "")))
                elif isinstance(data, list):
                    for m in data:
                        if vision_only and isinstance(m, dict) and "architecture" in m:
                            arch = m.get("architecture")
                            if isinstance(arch, dict):
                                mods = arch.get("input_modalities", [])
                                if isinstance(mods, list) and "image" not in mods:
                                    continue
                        if isinstance(m, dict):
                            models.append(m.get("id", m.get("model", "")))
                        else:
                            models.append(m)
                
                return True, sorted([str(m) for m in models if m])
            except Exception as e:
                return False, str(e)

        try:
            success, result = worker()
            if success:
                self.api_model_combo.addItems(result)
                if not result:
                    QMessageBox.warning(self, "Warning", "Provider returned an empty model list.")
            else:
                QMessageBox.critical(self, "Fetch Failed", f"Could not fetch models:\\n\\n{result}")
        finally:
            self.refresh_model_btn.setText("↻")
            self.refresh_model_btn.setEnabled(True)
            
        saved = settings.value("api_model", "gpt-4o")
        if self.api_model_combo.findText(saved) == -1:
            self.api_model_combo.insertItem(0, saved)
        self.api_model_combo.setCurrentText(saved)

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
    def export_type(self) -> str:
        return self.export_type_combo.currentData()

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
        self.cap_all_btn.setEnabled(not exporting)
        self.cap_missing_btn.setEnabled(not exporting)
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
    def _separator_thin() -> QWidget:
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #1E2A35; margin: 2px 0;")
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
    def _combo_editable_style() -> str:
        return """
            QComboBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                padding: 4px 8px;
                color: #D0DEE8;
                font-size: 11px;
            }
            QComboBox:hover { border-color: #00BCD4; }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #2A3A4A;
            }
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
    def _textedit_style() -> str:
        return """
            QTextEdit {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QTextEdit:hover { border-color: #00BCD4; }
            QTextEdit:focus { border-color: #00BCD4; }
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
