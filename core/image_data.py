"""Data model for image items in the PixelPrep desktop app."""

from dataclasses import dataclass, field


@dataclass
class ImageItem:
    """Represents a single image in the processing queue."""

    file_path: str
    scale: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    rotation: float = 0.0

    _original_width: int = field(default=0, repr=False, compare=False)
    _original_height: int = field(default=0, repr=False, compare=False)

    @property
    def filename(self) -> str:
        import os
        return os.path.basename(self.file_path)

    @property
    def filename_no_ext(self) -> str:
        import os
        name = os.path.basename(self.file_path)
        dot = name.rfind(".")
        return name[:dot] if dot != -1 else name

    @property
    def original_size(self) -> tuple[int, int]:
        return (self._original_width, self._original_height)
