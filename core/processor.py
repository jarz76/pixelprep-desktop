"""Multi-threaded batch image export engine."""

import os
import zipfile

from PIL import Image
from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class ExportResult:
    """Result of processing a single image."""

    def __init__(self, file_path: str, success: bool, error: str = ""):
        self.file_path = file_path
        self.success = success
        self.error = error


class _WorkerSignals(QObject):
    finished = pyqtSignal(object)


class ExportWorker(QRunnable):
    """Processes a single image: rotate → scale → crop → save."""

    def __init__(
        self,
        file_path: str,
        output_path: str,
        target_w: int,
        target_h: int,
        scale: float,
        pan_x: float,
        pan_y: float,
        rotation: float,
        output_format: str,
        sizing_mode: str,
        caption: str = "",
    ):
        super().__init__()
        self.file_path = file_path
        self.output_path = output_path
        self.target_w = target_w
        self.target_h = target_h
        self.scale = scale
        self.pan_x = pan_x
        self.pan_y = pan_y
        self.rotation = rotation
        self.output_format = output_format
        self.sizing_mode = sizing_mode
        self.caption = caption
        self.signals = _WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            img = Image.open(self.file_path)
            img = img.convert("RGBA")

            # Store original dimensions BEFORE rotation
            original_w, original_h = img.size
            target_aspect = self.target_w / self.target_h

            if self.sizing_mode == "fixed_size":
                # Scale image based on original dimensions
                fill_scale = max(self.target_w / original_w, self.target_h / original_h)
                actual_scale = fill_scale * self.scale
                scaled_w = int(original_w * actual_scale)
                scaled_h = int(original_h * actual_scale)
                img = img.resize((scaled_w, scaled_h), Image.LANCZOS)

                # Create output canvas with green background for unfilled areas
                output = Image.new("RGBA", (self.target_w, self.target_h), (0x38, 0xe1, 0x38, 255))

                if self.rotation != 0:
                    # Rotate the image around its center
                    img = img.rotate(-self.rotation, resample=Image.BICUBIC, expand=True)
                    rotated_w, rotated_h = img.size

                    # The rotation center in the preview is at:
                    # (target_w/2 + pan_x*actual_scale, target_h/2 + pan_y*actual_scale)
                    # This is where the center of the rotated image should be placed
                    center_x = self.target_w / 2 + self.pan_x * actual_scale
                    center_y = self.target_h / 2 + self.pan_y * actual_scale

                    # Paste position: place rotated image center at the rotation center
                    paste_x = center_x - rotated_w / 2
                    paste_y = center_y - rotated_h / 2
                else:
                    # No rotation: position image based on pan
                    # Image center goes at (target_w/2 + pan_x*actual_scale, target_h/2 + pan_y*actual_scale)
                    center_x = self.target_w / 2 + self.pan_x * actual_scale
                    center_y = self.target_h / 2 + self.pan_y * actual_scale
                    paste_x = center_x - scaled_w / 2
                    paste_y = center_y - scaled_h / 2

                output.paste(img, (int(paste_x), int(paste_y)), img if img.mode == "RGBA" else None)
                img = output

            else:  # fixed_aspect_ratio
                # Calculate crop dimensions based on target aspect ratio
                if original_w / original_h > target_aspect:
                    crop_h = original_h
                    crop_w = int(crop_h * target_aspect)
                else:
                    crop_w = original_w
                    crop_h = int(crop_w / target_aspect)

                # Apply scale (zoom)
                crop_w = min(int(crop_w / self.scale), original_w)
                crop_h = min(int(crop_h / self.scale), original_h)

                # Calculate crop position with pan offset
                cx = original_w / 2 - self.pan_x
                cy = original_h / 2 - self.pan_y

                left = max(0, min(int(cx - crop_w / 2), original_w - crop_w))
                top = max(0, min(int(cy - crop_h / 2), original_h - crop_h))
                right = left + crop_w
                bottom = top + crop_h

                img = img.crop((left, top, right, bottom))
                crop_w_actual = right - left
                crop_h_actual = bottom - top

                if self.rotation != 0:
                    # Create output canvas with green background for unfilled areas
                    output = Image.new("RGBA", (crop_w_actual, crop_h_actual), (0x38, 0xe1, 0x38, 255))
                    rotated = img.rotate(-self.rotation, resample=Image.BICUBIC, expand=True)
                    rw, rh = rotated.size
                    paste_x = crop_w_actual / 2 - rw / 2
                    paste_y = crop_h_actual / 2 - rh / 2
                    output.paste(rotated, (int(paste_x), int(paste_y)), rotated if rotated.mode == "RGBA" else None)
                    img = output

            # Save
            if self.output_format.lower() == "jpeg":
                img = img.convert("RGB")
                img.save(self.output_path, "JPEG", quality=95)
            else:
                img.save(self.output_path, "PNG")

            if self.caption and self.caption.strip():
                txt_path = os.path.splitext(self.output_path)[0] + ".txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(self.caption.strip())

            self.signals.finished.emit(ExportResult(self.file_path, True))
        except Exception as e:
            self.signals.finished.emit(ExportResult(self.file_path, False, str(e)))


class BatchExporter(QObject):
    """Manages multi-threaded batch export of all images."""

    progress = pyqtSignal(int, int)
    all_done = pyqtSignal(int, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._completed = 0
        self._succeeded = 0
        self._failed = 0
        self._total = 0

    def export_to_folder(self, items, output_dir, target_w, target_h,
                         output_format, sizing_mode):
        self._completed = 0
        self._succeeded = 0
        self._failed = 0
        self._total = len(items)

        if self._total == 0:
            self.all_done.emit(0, 0)
            return

        ext = "jpg" if output_format.lower() == "jpeg" else "png"
        used_names = set()

        for item in items:
            base_name = item.filename_no_ext
            out_name = f"{base_name}.{ext}"
            if out_name in used_names:
                import uuid
                out_name = f"{uuid.uuid4().hex[:8]}_{base_name}.{ext}"
            used_names.add(out_name)
            out_path = os.path.join(output_dir, out_name)

            worker = ExportWorker(
                file_path=item.file_path,
                output_path=out_path,
                target_w=target_w,
                target_h=target_h,
                scale=item.scale,
                pan_x=item.pan_x,
                pan_y=item.pan_y,
                rotation=item.rotation,
                output_format=output_format,
                sizing_mode=sizing_mode,
                caption=item.caption,
            )
            worker.signals.finished.connect(self._on_worker_finished)
            self._pool.start(worker)

    def export_to_zip(self, items, zip_path, target_w, target_h,
                      output_format, sizing_mode):
        import tempfile
        self._zip_path = zip_path
        self._tmp_dir = tempfile.mkdtemp(prefix="pixelprep_")
        self._is_zip_export = True

        self.export_to_folder(items, self._tmp_dir, target_w, target_h,
                              output_format, sizing_mode)

    def _on_worker_finished(self, result: ExportResult):
        if result.success:
            self._succeeded += 1
        else:
            self._failed += 1
            self.error_occurred.emit(f"Failed: {result.file_path}: {result.error}")

        self._completed += 1
        self.progress.emit(self._completed, self._total)

        if self._completed >= self._total:
            if getattr(self, "_is_zip_export", False):
                try:
                    self._create_zip()
                except Exception as e:
                    self.error_occurred.emit(f"Zip creation failed: {e}")
                finally:
                    import shutil
                    shutil.rmtree(self._tmp_dir, ignore_errors=True)
                    self._is_zip_export = False

            self.all_done.emit(self._succeeded, self._failed)

    def _create_zip(self):
        with zipfile.ZipFile(self._zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(self._tmp_dir):
                for fn in files:
                    full = os.path.join(root, fn)
                    zf.write(full, fn)


def generate_thumbnail(file_path: str, thumb_size: int = 200) -> tuple[bytes, int, int, int, int]:
    """Generate a thumbnail. Returns (rgba_bytes, tw, th, orig_w, orig_h)."""
    img = Image.open(file_path)
    orig_w, orig_h = img.size
    img.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
    img = img.convert("RGBA")
    tw, th = img.size
    return img.tobytes(), tw, th, orig_w, orig_h
