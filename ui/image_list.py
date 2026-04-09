"""Virtualized image grid with inline interactive cards — drag-to-pan, zoom, rotation."""

import os

from PyQt6.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QImage,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.image_data import ImageItem
from core.processor import generate_thumbnail

# ─── Thumbnail Loader (background) ─────────────────────────────


class _ThumbSignals(QWidget):
    loaded = pyqtSignal(str, object)  # file_path, QPixmap


class _ThumbWorker(QRunnable):
    """Load a single thumbnail in the background."""

    def __init__(self, file_path: str, thumb_size: int, signals: _ThumbSignals):
        super().__init__()
        self.file_path = file_path
        self.thumb_size = thumb_size
        self.signals = signals

    @pyqtSlot()
    def run(self):
        try:
            data, tw, th, ow, oh = generate_thumbnail(self.file_path, self.thumb_size)
            qimg = QImage(data, tw, th, tw * 4, QImage.Format.Format_RGBA8888).copy()
            pixmap = QPixmap.fromImage(qimg)
            self.signals.loaded.emit(self.file_path, (pixmap, ow, oh))
        except Exception:
            pass


# ─── Image Preview Widget (drag-to-pan, shows crop) ────────────


class ImagePreview(QWidget):
    """Custom-painted image preview with drag-to-pan. Shows the image
    inside a crop box matching the target output aspect ratio."""

    def __init__(self, item: ImageItem, target_w: int, target_h: int, parent=None):
        super().__init__(parent)
        self.item = item
        self.target_w = target_w
        self.target_h = target_h
        self._pixmap: QPixmap | None = None
        self._full_pixmap: QPixmap | None = None
        self._panning = False
        self._last_pos = QPointF()
        self._orig_w = 0
        self._orig_h = 0
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_pixmap(self, pixmap: QPixmap, orig_w: int, orig_h: int):
        """Set the loaded full-res pixmap."""
        self._full_pixmap = pixmap
        self._orig_w = orig_w
        self._orig_h = orig_h
        self.item._original_width = orig_w
        self.item._original_height = orig_h
        self.update()

    def set_target_size(self, w: int, h: int):
        self.target_w = w
        self.target_h = h
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()

        if not self._full_pixmap or self._full_pixmap.isNull():
            # Loading placeholder
            painter.fillRect(0, 0, w, h, QColor("#1A2530"))
            painter.setPen(QColor("#334455"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "Loading…")
            painter.end()
            return

        # Calculate the view: we simulate react-avatar-editor behavior
        # The preview area shows the image scaled+panned with the crop region visible
        target_aspect = self.target_w / self.target_h
        preview_aspect = w / h

        # The crop box fills the preview widget (like react-avatar-editor)
        # Image scale=1.0 means the image is scaled to just fill the crop box
        img_w, img_h = self._orig_w, self._orig_h

        # Base scale: fill the crop box
        fill_scale = max(self.target_w / img_w, self.target_h / img_h)
        actual_scale = fill_scale * self.item.scale

        # Scale from target coords to widget coords
        widget_scale_x = w / self.target_w
        widget_scale_y = h / self.target_h
        widget_scale = min(widget_scale_x, widget_scale_y)

        # Draw the image transformed
        painter.save()

        # Center the view
        ox = (w - self.target_w * widget_scale) / 2
        oy = (h - self.target_h * widget_scale) / 2
        painter.translate(ox, oy)
        painter.scale(widget_scale, widget_scale)

        # Clip to the crop box
        painter.setClipRect(QRectF(0, 0, self.target_w, self.target_h))

        # Draw bright green background for visible empty areas when rotated
        painter.fillRect(QRectF(0, 0, self.target_w, self.target_h), QColor("#38e138"))

        # Draw the image centered in the crop box with scale and pan
        img_draw_w = img_w * actual_scale
        img_draw_h = img_h * actual_scale
        img_x = (self.target_w - img_draw_w) / 2 + self.item.pan_x * actual_scale
        img_y = (self.target_h - img_draw_h) / 2 + self.item.pan_y * actual_scale

        if self.item.rotation != 0:
            # Rotate around center of drawn image
            center_x = img_x + img_draw_w / 2
            center_y = img_y + img_draw_h / 2
            painter.translate(center_x, center_y)
            painter.rotate(self.item.rotation)
            painter.translate(-center_x, -center_y)

        painter.drawPixmap(QRectF(img_x, img_y, img_draw_w, img_draw_h), self._full_pixmap,
                           QRectF(0, 0, self._full_pixmap.width(), self._full_pixmap.height()))

        painter.restore()

        # Border removed per user request

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.position() - self._last_pos
            self._last_pos = event.position()

            # Convert screen delta to image pan coordinates
            w, h = self.width(), self.height()
            widget_scale = min(w / self.target_w, h / self.target_h)
            fill_scale = 1.0
            if self._orig_w > 0 and self._orig_h > 0:
                fill_scale = max(self.target_w / self._orig_w, self.target_h / self._orig_h)
            actual_scale = fill_scale * self.item.scale

            if actual_scale > 0 and widget_scale > 0:
                self.item.pan_x += delta.x() / (widget_scale * actual_scale)
                self.item.pan_y += delta.y() / (widget_scale * actual_scale)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def wheelEvent(self, event: QWheelEvent):
        # Forward wheel to parent card's zoom slider
        parent_card = self.parent()
        if hasattr(parent_card, '_on_preview_scroll'):
            parent_card._on_preview_scroll(event.angleDelta().y())


# ─── Image Card Widget ──────────────────────────────────────────


class ImageCard(QWidget):
    """A single image card with inline preview, zoom slider, rotation slider,
    delete and save buttons — matching the web app's per-card layout."""

    delete_requested = pyqtSignal(object)  # emits self
    save_requested = pyqtSignal(object)    # emits self

    def __init__(self, item: ImageItem, target_w: int, target_h: int, parent=None):
        super().__init__(parent)
        self.item = item
        self.target_w = target_w
        self.target_h = target_h
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            ImageCard {
                background: #1A2535;
                border-radius: 12px;
                border: 1px solid #253545;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Preview area ────────────────────────────
        self.preview = ImagePreview(self.item, self.target_w, self.target_h, self)
        self.preview.setMinimumHeight(120)
        self.preview.setMouseTracking(True)
        layout.addWidget(self.preview, 1)

        # ── Controls area ───────────────────────────
        controls = QWidget()
        controls.setStyleSheet("background: #1A2535; border-top: 1px solid #253545; border-radius: 0 0 12px 12px;")
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(10, 8, 10, 10)
        ctrl_layout.setSpacing(4)

        # Filename + buttons row
        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        self._name_edit = QLineEdit(self.item.filename_no_ext)
        self._name_edit.setReadOnly(True)
        self._name_edit.setStyleSheet("""
            QLineEdit {
                background: #141E28;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                color: #C0D0E0;
                font-size: 11px;
                font-weight: 500;
                padding: 3px 6px;
            }
            QLineEdit:focus { border-color: #3A4A5A; }
        """)
        self._name_edit.setCursor(Qt.CursorShape.IBeamCursor)
        name_row.addWidget(self._name_edit, 1)

        save_btn = QPushButton("💾")
        save_btn.setFixedSize(26, 26)
        save_btn.setToolTip("Save this image")
        save_btn.setStyleSheet(self._icon_btn_style())
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(lambda: self.save_requested.emit(self))
        name_row.addWidget(save_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setToolTip("Remove image")
        del_btn.setStyleSheet(self._icon_btn_del_style())
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        name_row.addWidget(del_btn)

        ctrl_layout.addLayout(name_row)

        # Zoom row
        zoom_row = QHBoxLayout()
        zoom_row.setSpacing(6)
        zoom_icon = QLabel("🔍")
        zoom_icon.setFixedWidth(18)
        zoom_icon.setStyleSheet("font-size: 11px;")
        zoom_row.addWidget(zoom_icon)

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(100, 400)
        self._zoom_slider.setValue(int(self.item.scale * 100))
        self._zoom_slider.setStyleSheet(self._slider_style())
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        zoom_row.addWidget(self._zoom_slider, 1)

        self._zoom_spin = QSpinBox()
        self._zoom_spin.setRange(100, 400)
        self._zoom_spin.setValue(int(self.item.scale * 100))
        self._zoom_spin.setSuffix("%")
        self._zoom_spin.setFixedWidth(50)
        self._zoom_spin.setStyleSheet(self._spin_style())
        self._zoom_spin.valueChanged.connect(self._on_zoom_spin_changed)
        zoom_row.addWidget(self._zoom_spin)
        ctrl_layout.addLayout(zoom_row)

        # Rotation row
        rot_row = QHBoxLayout()
        rot_row.setSpacing(6)
        rot_icon = QLabel("🔄")
        rot_icon.setFixedWidth(18)
        rot_icon.setStyleSheet("font-size: 11px;")
        rot_row.addWidget(rot_icon)

        self._rot_slider = QSlider(Qt.Orientation.Horizontal)
        self._rot_slider.setRange(-180, 180)
        self._rot_slider.setValue(int(self.item.rotation))
        self._rot_slider.setStyleSheet(self._slider_style())
        self._rot_slider.valueChanged.connect(self._on_rot_slider_changed)
        rot_row.addWidget(self._rot_slider, 1)

        self._rot_spin = QSpinBox()
        self._rot_spin.setRange(-180, 180)
        self._rot_spin.setValue(int(self.item.rotation))
        self._rot_spin.setSuffix("°")
        self._rot_spin.setFixedWidth(50)
        self._rot_spin.setStyleSheet(self._spin_style())
        self._rot_spin.valueChanged.connect(self._on_rot_spin_changed)
        rot_row.addWidget(self._rot_spin)
        ctrl_layout.addLayout(rot_row)

        # Caption text area
        self._caption_edit = QTextEdit()
        self._caption_edit.setPlaceholderText("Enter caption...")
        self._caption_edit.setText(self.item.caption)
        self._caption_edit.setFixedHeight(70)
        self._caption_edit.setStyleSheet("""
            QTextEdit {
                background: #141E28;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                color: #C0D0E0;
                font-size: 11px;
                padding: 4px;
            }
            QTextEdit:focus { border-color: #00BCD4; }
        """)
        self._caption_edit.textChanged.connect(self._on_caption_changed)
        ctrl_layout.addWidget(self._caption_edit)

        layout.addWidget(controls)

    def set_pixmap(self, pixmap: QPixmap, orig_w: int, orig_h: int):
        self.preview.set_pixmap(pixmap, orig_w, orig_h)

    def update_target_size(self, w: int, h: int):
        self.target_w = w
        self.target_h = h
        self.preview.set_target_size(w, h)

    def _on_zoom_slider_changed(self, value: int):
        self.item.scale = value / 100.0
        self._zoom_spin.blockSignals(True)
        self._zoom_spin.setValue(value)
        self._zoom_spin.blockSignals(False)
        self.preview.update()

    def _on_zoom_spin_changed(self, value: int):
        self.item.scale = value / 100.0
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(value)
        self._zoom_slider.blockSignals(False)
        self.preview.update()

    def _on_rot_slider_changed(self, value: int):
        self.item.rotation = float(value)
        self._rot_spin.blockSignals(True)
        self._rot_spin.setValue(value)
        self._rot_spin.blockSignals(False)
        self.preview.update()

    def _on_rot_spin_changed(self, value: int):
        self.item.rotation = float(value)
        self._rot_slider.blockSignals(True)
        self._rot_slider.setValue(value)
        self._rot_slider.blockSignals(False)
        self.preview.update()

    def _on_caption_changed(self):
        self.item.caption = self._caption_edit.toPlainText()

    def _on_preview_scroll(self, delta_y: int):
        step = 5 if delta_y > 0 else -5
        new_val = max(self._zoom_slider.minimum(),
                      min(self._zoom_slider.maximum(), self._zoom_slider.value() + step))
        self._zoom_slider.setValue(new_val)

    @staticmethod
    def _slider_style() -> str:
        return """
            QSlider { height: 18px; }
            QSlider::groove:horizontal {
                background: #253545;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00BCD4;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover { background: #26C6DA; }
            QSlider::sub-page:horizontal {
                background: #00838F;
                border-radius: 2px;
            }
        """

    @staticmethod
    def _spin_style() -> str:
        return """
            QSpinBox {
                background: #1E2A35;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                padding: 2px 2px;
                color: #AABBCC;
                font-size: 11px;
            }
            QSpinBox:hover { border-color: #00BCD4; }
            QSpinBox:focus { border-color: #00BCD4; }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                border: none;
            }
        """

    @staticmethod
    def _icon_btn_style() -> str:
        return """
            QPushButton {
                background: transparent;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                color: #8899AA;
                font-size: 12px;
            }
            QPushButton:hover { border-color: #00BCD4; color: #00BCD4; }
        """

    @staticmethod
    def _icon_btn_del_style() -> str:
        return """
            QPushButton {
                background: transparent;
                border: 1px solid #2A3A4A;
                border-radius: 4px;
                color: #667788;
                font-size: 11px;
            }
            QPushButton:hover { border-color: #FF5555; color: #FF5555; background: #2A1515; }
        """


# ─── Flow Layout ────────────────────────────────────────────────


class FlowLayout(QVBoxLayout):
    """Simple flow layout that arranges child widgets in rows that wrap."""

    # We'll use a flat QVBoxLayout approach: we manually position widgets
    # This is actually implemented via the parent widget's resizeEvent
    pass


# ─── Image List Widget ──────────────────────────────────────────


class ImageListWidget(QWidget):
    """Main image area with flow-arranged interactive cards and drag-and-drop."""

    images_changed = pyqtSignal()

    BASE_CARD_W = 240  # base width, can be overridden

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[ImageItem] = []
        self._cards: list[ImageCard] = []
        self._pixmap_cache: dict[str, tuple[QPixmap, int, int]] = {}
        self._target_w = 512
        self._target_h = 512
        self._card_width = 240  # current card width (can be changed)
        self._thumb_signals = _ThumbSignals()
        self._thumb_signals.loaded.connect(self._on_thumb_loaded)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { background: #0F1923; border: none; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: #0F1923;")
        self._scroll.setWidget(self._container)

        # Accept drops on the scroll area
        self._scroll.setAcceptDrops(True)
        self._scroll.dragEnterEvent = self._drag_enter
        self._scroll.dragMoveEvent = self._drag_move
        self._scroll.dropEvent = self._drop

        layout.addWidget(self._scroll)

        # Empty state - overlay on top of scroll area
        self._empty_label = QLabel(self)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("""
            QLabel {
                color: #445566;
                font-size: 16px;
                background: transparent;
                border: 3px dashed #2A3A4A;
                border-radius: 16px;
                padding: 60px 40px;
            }
        """)
        self._empty_label.setText(
            "🖼️\n\nDrop image files here\nor use 'Add Files' button\n\nSupports: JPG, PNG, WEBP"
        )
        self._empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._update_empty_state()

        # Notification overlay - for "No images found"
        self._notif_label = QLabel(self)
        self._notif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._notif_label.setStyleSheet("""
            QLabel {
                color: #FF6B6B;
                font-size: 14px;
                font-weight: 500;
                background: rgba(30, 40, 55, 0.95);
                border-radius: 8px;
                padding: 16px 24px;
            }
        """)
        self._notif_label.setText("⚠️ No images found")
        self._notif_label.setVisible(False)
        self._notif_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Loading progress overlay
        self._loading_container = QWidget(self)
        self._loading_container.setStyleSheet("""
            QWidget {
                background: rgba(15, 25, 35, 0.9);
                border-radius: 12px;
            }
        """)
        self._loading_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        loading_layout = QVBoxLayout(self._loading_container)
        loading_layout.setContentsMargins(20, 16, 20, 16)
        loading_layout.setSpacing(8)

        self._loading_label = QLabel("Loading images...")
        self._loading_label.setStyleSheet("color: #AABBCC; font-size: 12px; background: transparent;")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self._loading_label)

        self._loading_progress = QProgressBar()
        self._loading_progress.setRange(0, 100)
        self._loading_progress.setValue(0)
        self._loading_progress.setTextVisible(True)
        self._loading_progress.setFormat("%v / %m")
        self._loading_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #253545;
                height: 22px;
                text-align: center;
                color: #FFFFFF;
                font-size: 12px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BCD4, stop:1 #26C6DA);
                border-radius: 4px;
            }
        """)
        loading_layout.addWidget(self._loading_progress)
        self._loading_container.setVisible(False)

    def showEvent(self, event):
        super().showEvent(event)
        # Position empty label after widget is shown
        self._position_empty_label()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()
        self._position_empty_label()
        self._position_overlays()

    def _position_empty_label(self):
        if self._empty_label.isVisible():
            sw = self.width()
            sh = self.height()
            w = min(400, sw - 60)
            h = 220
            x = (sw - w) // 2
            y = (sh - h) // 2
            self._empty_label.setGeometry(x, y, w, h)

    def _position_overlays(self):
        sw = self.width()
        sh = self.height()

        # Position notification label
        if self._notif_label.isVisible():
            self._notif_label.adjustSize()
            w = self._notif_label.width()
            h = self._notif_label.height()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self._notif_label.setGeometry(x, y, w, h)
            self._notif_label.raise_()

        # Position loading container
        if self._loading_container.isVisible():
            w = 200
            h = 70
            x = (sw - w) // 2
            y = (sh - h) // 2
            self._loading_container.setGeometry(x, y, w, h)
            self._loading_container.raise_()

    def show_notification(self, message: str = "⚠️ No images found", duration_ms: int = 2500, is_success: bool = False):
        """Show a temporary notification overlay."""
        color = "#4CAF50" if is_success else "#FF6B6B"
        self._notif_label.setText(message)
        self._notif_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 14px;
                font-weight: 500;
                background: rgba(30, 40, 55, 0.95);
                border-radius: 8px;
                padding: 16px 24px;
            }}
        """)
        self._notif_label.setVisible(True)
        self._notif_label.adjustSize()
        self._position_overlays()
        # Auto-hide after duration
        QTimer.singleShot(duration_ms, self._hide_notification)

    def _hide_notification(self):
        self._notif_label.setVisible(False)

    def show_loading(self, total: int):
        """Show loading progress overlay."""
        self._loading_progress.setRange(0, total)
        self._loading_progress.setValue(0)
        self._loading_container.setVisible(True)
        self._empty_label.setVisible(False)  # Hide placeholder while loading
        self._position_overlays()

    def update_loading_progress(self, current: int):
        """Update the loading progress bar."""
        self._loading_progress.setValue(current)

    def hide_loading(self):
        """Hide loading progress overlay."""
        self._loading_container.setVisible(False)
        self._update_empty_state()  # Restore placeholder visibility

    def _update_empty_state(self):
        self._empty_label.setVisible(len(self._items) == 0)
        if len(self._items) == 0:
            self._empty_label.raise_()
            self._position_empty_label()

    def _reflow(self):
        """Position all cards in a flow layout inside the container."""
        if not self._cards:
            self._container.setMinimumHeight(0)
            return

        # Base card size based on target aspect ratio
        base_card_w = self._card_width
        target_aspect = self._target_w / self._target_h
        preview_h = int(base_card_w / target_aspect) if target_aspect > 0 else base_card_w
        preview_h = max(100, min(preview_h, 400))  # clamp
        base_card_h = preview_h + 140  # controls height

        container_w = self._scroll.viewport().width()
        if container_w <= 0:
            container_w = self.width() - 20

        padding = 16
        spacing = 12
        usable_w = container_w - padding * 2

        # Calculate number of columns
        cols = max(1, (usable_w + spacing) // (base_card_w + spacing))

        # Expand card width to fill the row (up to 15% larger)
        total_grid_w = cols * base_card_w + (cols - 1) * spacing
        leftover = usable_w - total_grid_w
        expand_per_card = min(leftover / cols, base_card_w * 0.15)
        card_w = int(base_card_w + expand_per_card)

        # Calculate preview height from card width and target aspect ratio
        preview_h = int(card_w / target_aspect) if target_aspect > 0 else card_w

        # Clamp preview height, and adjust card width to match
        max_preview_h = 400
        if preview_h > max_preview_h:
            preview_h = max_preview_h
            # Adjust card width to maintain aspect ratio with clamped height
            card_w = int(preview_h * target_aspect) if target_aspect > 0 else preview_h
            # Recalculate columns with adjusted card width
            cols = max(1, (usable_w + spacing) // (card_w + spacing))

        preview_h = max(100, preview_h)
        card_h = preview_h + 140

        # Center the grid horizontally
        total_grid_w = cols * card_w + (cols - 1) * spacing
        start_x = padding + max(0, (usable_w - total_grid_w) // 2)

        x = start_x
        y = padding
        col = 0

        for card in self._cards:
            card.setGeometry(x, y, card_w, card_h)
            card.setVisible(True)
            col += 1
            if col >= cols:
                col = 0
                x = start_x
                y += card_h + spacing
            else:
                x += card_w + spacing

        total_rows = (len(self._cards) + cols - 1) // cols
        total_h = padding * 2 + total_rows * card_h + max(0, total_rows - 1) * spacing
        self._container.setMinimumHeight(total_h)

    # ── Public API ──────────────────────────────────────────

    @property
    def items(self) -> list[ImageItem]:
        return self._items

    @property
    def count(self) -> int:
        return len(self._items)

    def set_target_size(self, w: int, h: int):
        self._target_w = w
        self._target_h = h
        for card in self._cards:
            card.update_target_size(w, h)
        self._reflow()

    def update_item_caption(self, item: ImageItem):
        for card in self._cards:
            if card.item == item:
                card._caption_edit.blockSignals(True)
                card._caption_edit.setText(item.caption)
                card._caption_edit.blockSignals(False)
                break

    def set_card_width(self, width: int):
        """Set the base card width for the grid preview."""
        self._card_width = width
        self._reflow()

    def add_files(self, file_paths: list[str]):
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

        # Filter valid image files first
        valid_files = []
        for fp in file_paths:
            ext = os.path.splitext(fp)[1].lower()
            if ext in valid_exts and os.path.isfile(fp):
                valid_files.append(fp)

        # Show notification if no valid images found
        if not valid_files:
            self.show_notification("⚠️ No images found")
            return

        # Show loading progress if many files
        total_count = len(valid_files)
        if total_count > 10:
            self.show_loading(total_count)

        loaded_count = 0
        for fp in valid_files:
            item = ImageItem(file_path=fp)
            self._items.append(item)

            card = ImageCard(item, self._target_w, self._target_h, self._container)
            card.delete_requested.connect(self._on_card_delete)
            card.save_requested.connect(self._on_card_save)
            self._cards.append(card)

            # Check cache first, otherwise load in background
            if fp in self._pixmap_cache:
                px, ow, oh = self._pixmap_cache[fp]
                card.set_pixmap(px, ow, oh)
            else:
                worker = _ThumbWorker(fp, max(800, self._target_w, self._target_h), self._thumb_signals)
                QThreadPool.globalInstance().start(worker)

            loaded_count += 1
            if total_count > 10:
                self.update_loading_progress(loaded_count)

        # Hide loading after done
        if total_count > 10:
            self.hide_loading()

        self._reflow()
        self._update_empty_state()
        self.images_changed.emit()

    def remove_item_by_card(self, card: ImageCard):
        if card in self._cards:
            idx = self._cards.index(card)
            self._items.pop(idx)
            self._cards.pop(idx)
            card.setParent(None)
            card.deleteLater()
            self._reflow()
            self._update_empty_state()
            self.images_changed.emit()

    def clear_all(self):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._items.clear()
        self._reflow()
        self._update_empty_state()
        self.images_changed.emit()

    # ── Drag & Drop ─────────────────────────────────────────

    def _drag_enter(self, event: QDragEnterEvent):
        if event.mimeData() and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _drag_move(self, event):
        if event.mimeData() and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event: QDropEvent):
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
                self.add_files(paths)
            event.acceptProposedAction()

    # ── Slots ───────────────────────────────────────────────

    @pyqtSlot(str, object)
    def _on_thumb_loaded(self, file_path: str, result: tuple):
        pixmap, orig_w, orig_h = result
        self._pixmap_cache[file_path] = (pixmap, orig_w, orig_h)

        # Update any cards with this file path
        for card in self._cards:
            if card.item.file_path == file_path:
                card.set_pixmap(pixmap, orig_w, orig_h)

    def _on_card_delete(self, card: ImageCard):
        self.remove_item_by_card(card)

    def _on_card_save(self, card: ImageCard):
        """Save a single image with current settings."""
        from core.processor import ExportWorker

        item = card.item
        ext = "jpg" if hasattr(self, '_output_format') and self._output_format == "jpeg" else "png"
        fmt = getattr(self, '_output_format', 'png')
        mode = getattr(self, '_sizing_mode', 'fixed_size')

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            f"{item.filename_no_ext}.{ext}",
            f"Images (*.{ext})",
        )
        if not save_path:
            return

        worker = ExportWorker(
            file_path=item.file_path,
            output_path=save_path,
            target_w=self._target_w,
            target_h=self._target_h,
            scale=item.scale,
            pan_x=item.pan_x,
            pan_y=item.pan_y,
            rotation=item.rotation,
            output_format=fmt,
            sizing_mode=mode,
        )
        QThreadPool.globalInstance().start(worker)

    def set_output_settings(self, output_format: str, sizing_mode: str):
        """Called by main window when sidebar settings change."""
        self._output_format = output_format
        self._sizing_mode = sizing_mode
