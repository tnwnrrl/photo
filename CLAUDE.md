# Canon 100D Photo Processing System - Development Guide

**For AI assistants working on this codebase**

## Project Overview

Python application that monitors a Canon EOS 100D camera via USB, automatically downloads new photos, and composites them with a PNG overlay layer. Features a tkinter GUI for user control and persistent configuration.

## Common Commands

```bash
# Launch application (recommended)
./start.command

# Manual GUI launch
./venv/bin/python gui.py

# Build macOS executable
./build_mac.sh

# Test camera connection
./venv/bin/python -c "
from utils.camera import CameraConnection
camera = CameraConnection()
print('✅ Connected' if camera.connect() else '❌ Failed')
camera.disconnect()
"
```

## Architecture

### Core Components

**gui.py** - Main application entry point
- `PhotoProcessorGUI` class: tkinter-based GUI with monitoring controls
- Path selection UI for folders and overlay image (persistent via config.json)
- Reconnect button with automatic camera process cleanup
- Real-time log display using ScrolledText widget
- Monitoring loop runs in separate thread to prevent GUI freeze

**main.py** - CLI processing logic (can run standalone or via GUI)
- `PhotoProcessor` class: Core monitoring and processing orchestration
- Reads config.json for all paths and settings
- Maintains processed_files.json to prevent duplicate processing
- 5-second polling loop checking for new camera files

**utils/camera.py** - Canon camera interface
- `CameraConnection` class: gphoto2 wrapper with context manager support
- `get_all_files()`: Lists all JPEG files on camera
- `download_file()`: Downloads specific file to local folder
- Handles gphoto2 errors gracefully

**utils/image_processor.py** - Image composition engine
- `ImageProcessor` class: Pillow-based PNG overlay composition
- Handles automatic image resizing (overlay resized to match base photo)
- RGBA alpha compositing for transparency preservation
- Saves with JPEG quality=95 for high-quality output

### Data Flow

```
Camera (Canon 100D)
    ↓ USB (gphoto2)
CameraConnection.get_all_files()
    ↓
PhotoProcessor.process_new_photos()
    ↓ Download to original_folder
CameraConnection.download_file()
    ↓
ImageProcessor.add_overlay()
    ↓ Composite with overlay.png
Save to output_folder
    ↓
Update processed_files.json
```

### Configuration System

**config.json** - All runtime settings
```json
{
  "camera": {
    "model": "Canon EOS 100D",
    "check_interval_seconds": 5
  },
  "paths": {
    "original_folder": "downloaded_photos",
    "overlay_image": "overlay.png",
    "output_folder": "processed_photos"
  }
}
```

GUI writes to config.json when user changes paths. main.py and gui.py both read from it.

**processed_files.json** - Tracking database
```json
{
  "IMG_1234.JPG": "2025-11-08T10:30:15",
  "IMG_1235.JPG": "2025-11-08T10:35:22"
}
```

Prevents reprocessing same file across application restarts.

## Critical Technical Constraints

### macOS Camera Connection Issues

**Root Cause**: macOS system processes (`ptpcamerad`, `mscamerad-xpc`, `icdd`, `cameracaptured`) automatically claim USB camera devices and restart via launchd when killed.

**Error**: `[-53] Could not claim the USB device (GP_ERROR_IO_USB_CLAIM)`

**Race Condition**: 50-100ms timing window between process kill and launchd restart. gphoto2 must claim USB device during this window.

**Solution Strategy** (implemented in start.command):
1. Kill all camera processes with `pkill -9`
2. Immediately attempt camera connection
3. Retry up to 3 times with 2-second delays
4. Success rate: 70-80%

**Workarounds**:
- Physical USB reconnection (5-second wait): 80-90% success
- Change camera USB mode from PTP to Mass Storage: 90%+ success
- See TROUBLESHOOTING_ANALYSIS.md for comprehensive analysis

### start.command Implementation

Unified launcher that handles camera connection + GUI launch:

```bash
# 1. Kill conflicting processes
pkill -9 -f "ptpcamerad|mscamerad|icdd|cameracaptured"
killall -9 "Image Capture"

# 2. Retry camera connection (max 3 attempts)
for attempt in 1..3; do
  python -c "test camera connection"
  if success: break
  pkill camera processes again
  sleep 2
done

# 3. Launch GUI if connected
if connected:
  ./venv/bin/python gui.py
else:
  show error + troubleshooting steps
```

This is the **primary execution method** - all other launcher scripts have been removed.

## Build System

### macOS Executable

**build_mac.spec** - PyInstaller configuration:
- Entry point: gui.py
- Bundled data: config.json, overlay.png, utils/*.py
- Hidden imports: gphoto2, PIL, PIL._tkinter_finder
- Output: dist/Canon100D.app (~40MB)

**build_mac.sh** - Automated build:
```bash
source venv/bin/activate
rm -rf build dist
pyinstaller build_mac.spec --clean
```

**Windows Build**: Not supported - gphoto2 library unavailable for Windows. See BUILD_INSTRUCTIONS.md for alternatives (Canon SDK, remote camera control).

## Important Known Issues

### Overlay Image Transparency

**Issue**: If overlay.png is RGB mode (no alpha channel), composition will show only the overlay (100% opacity).

**Detection**:
```python
from PIL import Image
img = Image.open('overlay.png')
print(img.mode)  # Should be 'RGBA', not 'RGB'
```

**Fix**: Ensure overlay.png is RGBA mode with alpha channel for transparency. Create using `create_overlay.py` or convert existing RGB images.

**Current Code**: image_processor.py line 76-78 assumes RGBA overlay:
```python
result = base_image.copy()
result.paste(overlay, (0, 0), overlay)  # Third arg is alpha mask
```

### Camera Connection Reliability

Connection may fail on first attempt due to macOS process conflicts. **This is expected behavior**. start.command handles retries automatically.

**User Action Required**: If connection fails after 3 retries, physically reconnect USB cable and re-run start.command.

## Development Workflow

1. **Making Changes**: Work in feature branches, test with `./venv/bin/python gui.py`
2. **Testing Camera**: Use start.command for realistic connection testing
3. **Building**: Run `./build_mac.sh` to create standalone app
4. **Camera Issues**: Check TROUBLESHOOTING_ANALYSIS.md for detailed diagnostics

## Key Files Reference

- **gui.py** (400+ lines): Main GUI application
- **main.py** (200+ lines): Core processing logic
- **utils/camera.py** (150+ lines): Canon camera interface
- **utils/image_processor.py** (100+ lines): Image composition
- **start.command** (90+ lines): Unified launcher with retry logic
- **TROUBLESHOOTING_ANALYSIS.md** (340+ lines): Camera connection deep dive
- **BUILD_INSTRUCTIONS.md**: Executable build documentation
- **README.md**: User-facing documentation (Korean)

## Dependencies

- gphoto2: Canon camera communication (requires libgphoto2 via Homebrew)
- Pillow: Image processing and RGBA composition
- tkinter: GUI framework (bundled with Python)

Install: `pip install -r requirements.txt`

System: `brew install libgphoto2 pkg-config`
