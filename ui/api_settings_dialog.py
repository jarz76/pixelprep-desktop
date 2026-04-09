import json
import urllib.request
import ssl
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QWidget
)


class ApiSettingsDialog(QDialog):
    """Dialog for configuring the OpenRouter/OpenAI compatible API."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Configuration")
        self.setFixedSize(400, 320)
        self.setStyleSheet("""
            QDialog { background: #151E28; }
            QLabel { color: #AABBCC; font-size: 13px; font-weight: 500; }
            QLineEdit, QComboBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 6px;
                padding: 6px 10px;
                color: #D0DEE8;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #00BCD4; }
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
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                color: #D0DEE8;
                selection-background-color: #00BCD4;
            }
        """)

        self.settings = QSettings("PixelPrep", "Settings")
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Base URL
        layout.addWidget(QLabel("Base URL"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.openai.com")
        layout.addWidget(self.url_input)

        # API Key
        layout.addWidget(QLabel("API Key"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-...")
        layout.addWidget(self.key_input)

        layout.addStretch()

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(save_btn)
        
        layout.addLayout(btn_row)

    def _load_settings(self):
        self.url_input.setText(self.settings.value("api_url", "https://api.openai.com"))
        self.key_input.setText(self.settings.value("api_key", ""))

    def _save_and_close(self):
        self.settings.setValue("api_url", self.url_input.text().strip())
        self.settings.setValue("api_key", self.key_input.text().strip())
        self.accept()


