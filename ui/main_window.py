"""Main window assembling sidebar and image list."""

import os
from datetime import datetime

from PyQt6.QtCore import QPoint, Qt, QSettings
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.image_data import ImageItem
from core.processor import BatchExporter
from core.captioner import BatchCaptioner
from ui.image_list import ImageListWidget
from ui.sidebar import Sidebar


class TitleBar(QWidget):
    """Custom title bar with window controls."""

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self._main_window = parent
        self._drag_pos = None
        self.setFixedHeight(32)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("PixelPrep")
        title.setStyleSheet("""
            QLabel {
                color: #00BCD4;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Window control buttons
        btn_size = 28

        self._min_btn = QPushButton()
        self._min_btn.setFixedSize(btn_size, btn_size)
        self._min_btn.setText("─")
        self._min_btn.setStyleSheet(self._btn_style("#8899AA", "#AABBCC", "#253545"))
        self._min_btn.clicked.connect(self._main_window.showMinimized)
        layout.addWidget(self._min_btn)

        self._max_btn = QPushButton()
        self._max_btn.setFixedSize(btn_size, btn_size)
        self._max_btn.setText("□")
        self._max_btn.setStyleSheet(self._btn_style("#8899AA", "#AABBCC", "#253545"))
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        self._close_btn = QPushButton()
        self._close_btn.setFixedSize(btn_size, btn_size)
        self._close_btn.setText("✕")
        self._close_btn.setStyleSheet(self._btn_style("#8899AA", "#FF5555", "#2A1515", "#3A2A2A"))
        self._close_btn.clicked.connect(self._main_window.close)
        layout.addWidget(self._close_btn)

    def _toggle_maximize(self):
        if self._main_window.isMaximized():
            self._main_window.showNormal()
            self._max_btn.setText("□")
        else:
            self._main_window.showMaximized()
            self._max_btn.setText("❐")

    @staticmethod
    def _btn_style(color: str, hover_color: str, hover_bg: str, bg: str = "transparent") -> str:
        return f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: 4px;
                color: {color};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: {hover_color};
            }}
        """

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._main_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and not self._main_window.isMaximized():
            self._main_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()


class MainWindow(QMainWindow):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixelPrep — Bulk Resize & Crop")
        self.setMinimumSize(960, 640)
        self.resize(1280, 800)

        # Frameless window with custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._exporter = BatchExporter(self)
        self._exporter.progress.connect(self._on_export_progress)
        self._exporter.all_done.connect(self._on_export_done)
        self._exporter.error_occurred.connect(self._on_export_error)

        self._captioner = BatchCaptioner(self)
        self._captioner.progress.connect(self._on_export_progress)
        self._captioner.item_done.connect(self._on_caption_item_done)
        self._captioner.all_done.connect(self._on_caption_all_done)
        self._captioner.error_occurred.connect(self._on_export_error)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        container = QWidget()
        self.setCentralWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Custom title bar
        self._title_bar = TitleBar(self)
        self._title_bar.setStyleSheet("TitleBar { background: #151E28; }")
        container_layout.addWidget(self._title_bar)

        # Content area - no styling, lets children handle their own
        content = QWidget()
        container_layout.addWidget(content, 1)

        main_layout = QHBoxLayout(content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar - keep original styling
        self._sidebar = Sidebar()
        self._sidebar.setStyleSheet(
            "Sidebar { background: #151E28; border-right: 1px solid #2A3A4A; }"
        )
        main_layout.addWidget(self._sidebar)

        # Image list (the main content area)
        self._image_list = ImageListWidget()
        main_layout.addWidget(self._image_list, 1)

    def _connect_signals(self):
        # Sidebar → actions
        self._sidebar.add_files_clicked.connect(self._open_file_dialog)
        self._sidebar.add_folder_clicked.connect(self._open_folder_dialog)
        self._sidebar.clear_all_clicked.connect(self._clear_all_images)
        self._sidebar.export_clicked.connect(self._export_to_folder)
        self._sidebar.export_zip_clicked.connect(self._export_to_zip)
        self._sidebar.caption_all_clicked.connect(lambda: self._start_captioning(False))
        self._sidebar.caption_missing_clicked.connect(lambda: self._start_captioning(True))
        self._sidebar.replace_all_clicked.connect(self._replace_captions)
        self._sidebar.settings_changed.connect(self._on_settings_changed)
        self._sidebar.preview_size_changed.connect(self._image_list.set_card_width)

        # Image list → sidebar count
        self._image_list.images_changed.connect(
            lambda: self._sidebar.set_image_count(self._image_list.count)
        )

        # Initial settings push
        self._on_settings_changed()

    def _clear_all_images(self):
        self._image_list.clear_all()

    def _replace_captions(self, target: str, replacement: str):
        count = 0
        for item in self._image_list.items:
            if item.caption and target in item.caption:
                item.caption = item.caption.replace(target, replacement)
                self._image_list.update_item_caption(item)
                count += 1
        
        self._image_list.show_notification(f"✅ Replaced '{target}' with '{replacement}' in {count} captions", 3000, is_success=True)

    # ── Actions ─────────────────────────────────────────────

    def _open_file_dialog(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.jpg *.jpeg *.png *.webp);;All Files (*)",
        )
        if file_paths:
            self._image_list.add_files(file_paths)

    def _open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            paths = []
            for root, _, files in os.walk(folder_path):
                for fn in files:
                    paths.append(os.path.join(root, fn))
            if paths:
                self._image_list.add_files(paths)
            else:
                self._image_list.show_notification("⚠️ Folder is empty")

    def _on_settings_changed(self):
        self._image_list.set_target_size(
            self._sidebar.output_width,
            self._sidebar.output_height,
        )
        self._image_list.set_output_settings(
            self._sidebar.output_format,
            self._sidebar.output_mode,
        )

    def _export_to_folder(self):
        items = self._image_list.items
        if not items:
            self._image_list.show_notification("⚠️ No images to export", 2500)
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_dir:
            return

        self._sidebar.set_exporting(True, len(items))
        self._exporter.export_to_folder(
            items,
            output_dir,
            self._sidebar.output_width,
            self._sidebar.output_height,
            self._sidebar.output_format,
            self._sidebar.export_type,
            self._sidebar.output_mode,
        )

    def _export_to_zip(self):
        items = self._image_list.items
        if not items:
            self._image_list.show_notification("⚠️ No images to export", 2500)
            return

        template = self._sidebar.zip_filename_template
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = template.replace("{timestamp}", timestamp)
        if not filename.lower().endswith(".zip"):
            filename += ".zip"

        zip_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save ZIP File",
            filename,
            "ZIP Files (*.zip)",
        )
        if not zip_path:
            return

        self._sidebar.set_exporting(True, len(items))
        self._exporter.export_to_zip(
            items,
            zip_path,
            self._sidebar.output_width,
            self._sidebar.output_height,
            self._sidebar.output_format,
            self._sidebar.export_type,
            self._sidebar.output_mode,
        )

    # ── Export callbacks ────────────────────────────────────

    def _on_export_progress(self, completed: int, total: int):
        self._sidebar.update_progress(completed, total)

    def _start_captioning(self, skip_existing: bool):
        items = self._image_list.items
        if not items:
            self._image_list.show_notification("⚠️ No images to caption", 2500)
            return

        settings = QSettings("PixelPrep", "Settings")
        api_url = settings.value("api_url", "https://api.openai.com").strip()
        api_key = settings.value("api_key", "").strip()
        api_model = settings.value("api_model", "gpt-4o").strip()
        api_prompt = self._sidebar.api_prompt_edit.toPlainText().strip()
        
        if not api_url or not api_model:
            self._image_list.show_notification("⚠️ Please configure API URL and Model", 3000)
            return

        to_process = [it for it in items] if not skip_existing else [it for it in items if not it.caption.strip()]
        if not to_process:
            self._image_list.show_notification("⚠️ No missing captions found", 2500)
            return

        self._sidebar.set_exporting(True, len(to_process))
        self._captioner.start_captioning(
            items=items,
            target_w=self._sidebar.output_width,
            target_h=self._sidebar.output_height,
            sizing_mode=self._sidebar.output_mode,
            base_url=api_url,
            api_key=api_key,
            model=api_model,
            system_prompt=api_prompt,
            skip_existing=skip_existing
        )

    def _on_caption_item_done(self, item):
        self._image_list.update_item_caption(item)

    def _on_export_error(self, error_msg: str):
        print(f"Error: {error_msg}")
        if not hasattr(self, "_first_error") or not self._first_error:
            self._first_error = error_msg

    def _on_caption_all_done(self, succeeded: int, failed: int):
        self._sidebar.set_exporting(False)
        if failed == 0:
            self._image_list.show_notification(f"✅ Auto-caption complete! {succeeded} images captioned", 3000, is_success=True)
            self._first_error = None
        else:
            err_msg = getattr(self, "_first_error", "Unknown error")
            self._image_list.show_notification(f"⚠️ Captioning finished: {succeeded} succeeded, {failed} failed. Example error: {err_msg}", 5000, is_success=False)
            self._first_error = None

    def _on_export_done(self, succeeded: int, failed: int):
        self._sidebar.set_exporting(False)
        if failed == 0:
            self._image_list.show_notification(f"✅ Export complete! {succeeded} images saved", 3000, is_success=True)
            self._first_error = None
        else:
            self._image_list.show_notification(f"⚠️ Export finished: {succeeded} succeeded, {failed} failed", 5000, is_success=False)
            self._first_error = None

    # ── Window-level drag & drop ────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData() and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData() and event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    paths.append(path)
                elif os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for fn in files:
                            paths.append(os.path.join(root, fn))
            if paths:
                self._image_list.add_files(paths)
            event.acceptProposedAction()
