import json
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QListWidget,
    QTextEdit,
    QSplitter,
    QInputDialog,
    QMessageBox
)


class ApiSettingsDialog(QDialog):
    """Dialog for configuring the API and managing system prompt templates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Templates")
        self.setFixedSize(600, 440)
        self.setStyleSheet("""
            QDialog { background: #151E28; }
            QLabel { color: #AABBCC; font-size: 13px; font-weight: 500; }
            QLineEdit, QTextEdit, QListWidget {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QListWidget:focus { border-color: #00BCD4; }
            QPushButton {
                background: transparent;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 8px 16px;
                color: #8899AA;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }
            QPushButton#primaryBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4, stop:1 #0097A7);
                border: none;
                color: #FFFFFF;
            }
            QPushButton#primaryBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #26C6DA, stop:1 #00ACC1);
            }
            QTabWidget::pane { border: 1px solid #2A3A4A; border-radius: 4px; background: #1E2A35; }
            QTabBar::tab { background: #151E28; color: #8899AA; padding: 8px 16px; border: 1px solid #2A3A4A; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1E2A35; color: #00BCD4; }
            QListWidget::item:selected { background: #00BCD4; color: #ffffff; border-radius: 4px; }
        """)

        self.settings = QSettings("PixelPrep", "Settings")
        self.templates = {}
        self.current_selected_template = None
        
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        
        # Tab 1: Connection
        conn_tab = QWidget()
        conn_layout = QVBoxLayout(conn_tab)
        conn_layout.setContentsMargins(16, 16, 16, 16)
        conn_layout.setSpacing(12)
        
        conn_layout.addWidget(QLabel("Base URL"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.openai.com")
        conn_layout.addWidget(self.url_input)

        conn_layout.addWidget(QLabel("API Key"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-...")
        conn_layout.addWidget(self.key_input)
        conn_layout.addStretch()
        self.tabs.addTab(conn_tab, "Connection")

        # Tab 2: Prompt Templates
        tpl_tab = QWidget()
        tpl_layout = QVBoxLayout(tpl_tab)
        tpl_layout.setContentsMargins(16, 16, 16, 16)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: List and Buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        left_layout.addWidget(self.template_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        self.add_btn = QPushButton("+ Add")
        self.add_btn.clicked.connect(self._add_template)
        btn_layout.addWidget(self.add_btn)
        
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._rename_template)
        btn_layout.addWidget(self.rename_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_template)
        btn_layout.addWidget(self.delete_btn)
        
        left_layout.addLayout(btn_layout)
        splitter.addWidget(left_widget)
        
        # Right side: Text Editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlaceholderText("Enter system prompt here...")
        self.prompt_editor.textChanged.connect(self._on_prompt_edited)
        right_layout.addWidget(self.prompt_editor)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([180, 380])
        
        tpl_layout.addWidget(splitter)
        self.tabs.addTab(tpl_tab, "Prompt Templates")

        layout.addWidget(self.tabs)

        # Bottom buttons
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_and_close)
        bottom_row.addWidget(save_btn)
        
        layout.addLayout(bottom_row)

    def _load_settings(self):
        # Connection
        self.url_input.setText(self.settings.value("api_url", "https://api.openai.com"))
        self.key_input.setText(self.settings.value("api_key", ""))
        
        # Templates
        templates_json = self.settings.value("system_prompt_templates", "")
        if templates_json:
            try:
                self.templates = json.loads(templates_json)
            except:
                self.templates = {}
                
        if not self.templates:
            # Migration from old API prompt setting or safe default
            old_prompt = self.settings.value("api_prompt", "Describe this image in detail.")
            self.templates = {"Default": old_prompt}

        # Populate list
        self.template_list.clear()
        self.template_list.addItems(sorted(list(self.templates.keys())))
        
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

    def _on_template_selected(self, current, previous):
        if not current:
            self.prompt_editor.clear()
            self.prompt_editor.setEnabled(False)
            self.current_selected_template = None
            return
            
        self.prompt_editor.setEnabled(True)
        self.current_selected_template = current.text()
        prompt_text = self.templates.get(self.current_selected_template, "")
        
        # Disconnect momentarily to avoid marking as edited during load
        self.prompt_editor.blockSignals(True)
        self.prompt_editor.setText(prompt_text)
        self.prompt_editor.blockSignals(False)

    def _on_prompt_edited(self):
        if self.current_selected_template:
            self.templates[self.current_selected_template] = self.prompt_editor.toPlainText()

    def _add_template(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template Name:")
        if ok and name:
            name = name.strip()
            if not name:
                QMessageBox.warning(self, "Error", "Template name cannot be empty.")
                return
            if name in self.templates:
                QMessageBox.warning(self, "Error", "Template name already exists.")
                return
            self.templates[name] = ""
            self.template_list.addItem(name)
            
            # Select the newly added item
            items = self.template_list.findItems(name, Qt.MatchFlag.MatchExactly)
            if items:
                self.template_list.setCurrentItem(items[0])

    def _rename_template(self):
        item = self.template_list.currentItem()
        if not item:
            return
            
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Template", "New Template Name:", text=old_name)
        
        if ok and new_name:
            new_name = new_name.strip()
            if not new_name:
                QMessageBox.warning(self, "Error", "Template name cannot be empty.")
                return
            if new_name == old_name:
                return
            if new_name in self.templates:
                QMessageBox.warning(self, "Error", "Template name already exists.")
                return
                
            self.templates[new_name] = self.templates.pop(old_name)
            item.setText(new_name)
            self.current_selected_template = new_name
            
            # If renamed the active one, update it in settings (though not strictly needed until save)
            active_template = self.settings.value("system_prompt_active_template", "Default")
            if active_template == old_name:
                self.settings.setValue("system_prompt_active_template", new_name)

    def _delete_template(self):
        item = self.template_list.currentItem()
        if not item:
            return
            
        name = item.text()
        if len(self.templates) <= 1:
            QMessageBox.warning(self, "Warning", "Cannot delete the last template.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete template '{name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.templates.pop(name, None)
            row = self.template_list.row(item)
            self.template_list.takeItem(row)
            
            # Update active template if we just deleted it
            active_template = self.settings.value("system_prompt_active_template", "Default")
            if active_template == name:
                self.settings.setValue("system_prompt_active_template", list(self.templates.keys())[0])

    def _save_and_close(self):
        self.settings.setValue("api_url", self.url_input.text().strip())
        self.settings.setValue("api_key", self.key_input.text().strip())
        
        # Save templates
        self.settings.setValue("system_prompt_templates", json.dumps(self.templates))
        
        # Make sure the active template is valid
        active_template = self.settings.value("system_prompt_active_template", "Default")
        if active_template not in self.templates and self.templates:
            # if deleted or missing, pick first one available
            # Sort to be deterministic
            self.settings.setValue("system_prompt_active_template", sorted(list(self.templates.keys()))[0])
            
        self.accept()
