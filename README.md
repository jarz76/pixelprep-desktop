# PixelPrep Desktop

A fast, native desktop application for bulk image resizing and cropping with per-image pan, zoom, and rotation controls.

> **Note:** This desktop app is inspired by the UI design of [Presize.io](https://presize.io) - a web-based bulk image resizer. Check out the original web app at [github.com/kunchenguid/presize](https://github.com/kunchenguid/presize).

## Features

- **Drag & Drop Support** - Drop image files or entire folders directly into the app
- **Per-Image Controls** - Each image has its own zoom (100-400%), pan, and rotation (-180° to 180°) settings
- **Real-time Preview** - See exactly how your cropped/zoomed/rotated image will look before export
- **Two Output Modes**:
  - **Fixed Size** - All images output at exact dimensions (e.g., 512x512)
  - **Fixed Aspect Ratio** - Images maintain original resolution with target aspect ratio
- **Multiple Export Options**:
  - Export to folder
  - Export as ZIP file
  - Save individual images
- **Format Support** - JPG, PNG, WEBP input; PNG or JPEG output
- **Multi-threaded Processing** - Fast batch processing.

## Requirements

- Python 3.10+
- PyQt6
- Pillow

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pixelprep-desktop.git
cd pixelprep-desktop

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Adding Images

1. Click **Add Files** to select individual images
2. Click **Add Folder** to load all images from a directory (recursive)
3. Or simply **drag and drop** files/folders onto the main area

### Configuring Output

- **Width/Height** - Set target output dimensions
- **Output Mode**:
  - `Fixed Size` - Resizes all images to exact dimensions (may crop if aspect differs)
  - `Fixed Aspect Ratio` - Maintains maximum resolution with target aspect ratio
- **Format** - Choose PNG (lossless) or JPEG (compressed)

### Exporting

- **Export to Folder** - Save all processed images to a directory
- **Save as ZIP** - Package all images into a single ZIP file
- **Save Button** - Save a single image with current settings

## Project Structure

```
pixelprep-desktop/
├── main.py              # Entry point and dark theme setup
├── requirements.txt     # Python dependencies
├── core/
│   ├── __init__.py
│   ├── image_data.py    # Image item data model
│   └── processor.py     # Multi-threaded export engine
└── ui/
    ├── __init__.py
    ├── main_window.py   # Main window with custom title bar
    ├── sidebar.py       # Settings panel
    └── image_list.py    # Image grid with cards and preview
```

## Technical Details

- **PyQt6** - Modern Qt bindings for Python
- **Pillow** - Image processing (resize, crop, rotate)
- **QThreadPool** - Multi-threaded batch processing for fast exports
- **Custom Painting** - QPainter-based image preview with crop box visualization

## License

MIT License - feel free to use and modify.

## Acknowledgments

UI design inspired by [Presize.io](https://presize.io) and its open-source web application at [github.com/kunchenguid/presize](https://github.com/kunchenguid/presize).
