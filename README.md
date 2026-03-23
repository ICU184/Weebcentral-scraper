# WeebCentral Manager

A macOS desktop application for downloading manga chapters from [WeebCentral](https://weebcentral.com) as PDFs.

## Features

- **Add & Download** — Paste a WeebCentral series URL to download all chapters as individual PDFs
- **Bulk Update** — Automatically check all saved series for new chapters and download only what's missing
- **Manga List** — URLs are saved to `manga_list.txt` so you never have to re-enter them
- **GUI & CLI** — Use the standalone macOS app (no Python required) or run the scripts directly from the terminal

## Installation

### Option 1: Standalone App (Recommended)

Download `WeebCentral Manager UI.app` from the [Releases](../../releases) page.

> **First Launch on macOS:**
> Because the app is not from the Mac App Store, Gatekeeper will block it.
> **Right-click** the app → click **Open** → click **Open** on the warning dialog.
>
> If macOS says the app is "damaged", open Terminal and run:
> ```bash
> xattr -cr /path/to/WeebCentral\ Manager\ UI.app
> ```

### Option 2: Run from Source

Requires Python 3 and pip.

```bash
# Clone the repo
git clone https://github.com/YourUsername/WeebCentral-Manager.git
cd WeebCentral-Manager

# Install dependencies
chmod +x setup.sh
./setup.sh

# Run the terminal version
python3 weebcentral_scraper.py
```

## Usage

### GUI App
1. Open **WeebCentral Manager UI.app**
2. Paste a WeebCentral series URL into the text field and click **Add & Download**
3. Or click **Update All Missing Chapters** to bulk-update every series in your list
4. Progress is displayed directly in the app window

### Terminal
```bash
python3 weebcentral_scraper.py
```
You will be prompted to choose:
```
WeebCentral Manager
-------------------
1) Add a new manga URL to your list and download it
2) Update all manga currently in your list

Enter 1 or 2:
```

## Where Are My Files?

All downloads are saved to:
```
~/Documents/WeebCentral/
```

Each series gets its own folder containing:
```
~/Documents/WeebCentral/
├── manga_list.txt
├── series-name/
│   ├── pdfs/
│   │   ├── series-name - Chapter 0001.pdf
│   │   ├── series-name - Chapter 0002.pdf
│   │   └── ...
│   └── images/
│       └── chapter_0001/
│           ├── 0001-001.png
│           └── ...
└── another-series/
    └── ...
```

## Building the App Yourself

If you want to compile the `.app` bundle from source:

```bash
# Create a virtual environment and install build deps
python3 -m venv venv
source venv/bin/activate
pip install PySide6 pyinstaller requests Pillow

# Build the app
pyinstaller --clean --windowed \
  --hidden-import requests \
  --hidden-import PIL \
  --hidden-import PIL.Image \
  --name="WeebCentral Manager UI" gui.py

# Fix macOS code signing
xattr -cr "dist/WeebCentral Manager UI.app"
codesign --force --deep -s - "dist/WeebCentral Manager UI.app"
```

> **Note:** The built app targets **Apple Silicon (arm64)**. It will run on Intel Macs via Rosetta 2.

## Project Structure

| File | Description |
|---|---|
| `weebcentral_scraper.py` | Core scraping logic and CLI interface |
| `gui.py` | PySide6 graphical interface wrapper |
| `bulk_manga_updater.py` | Legacy standalone bulk updater (functionality now in main scraper) |
| `setup.sh` | macOS setup script for running from source |
| `requirements.txt` | Python dependencies |
| `instructions.txt` | End-user installation guide |

## Requirements

- **Standalone App:** macOS (Apple Silicon or Intel with Rosetta 2)
- **From Source:** Python 3.6+, `requests`, `Pillow`
- **Building the App:** Above + `PySide6`, `PyInstaller`

## License

This project is provided as-is for personal use.
