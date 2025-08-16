# Video Downloader Application

A desktop application for downloading videos from YouTube and Instagram, built with Python and Flet.

## Features
- Download YouTube videos in various formats
- Download Instagram videos/reels
- Download history tracking
- Dark/light mode toggle
- Progress indicators
- Threaded downloads

## Installation
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
```bash
python Downloader.py
```

### YouTube Download
1. Paste YouTube URL
2. Click "Fetch Formats"
3. Select desired format from table
4. Click "Download Selected"

### Instagram Download
1. Paste Instagram URL
2. Click "Download Video"

## Notes
- Downloaded files are saved to your Downloads folder by default
- History is stored in `~/.flet_video_downloader_history.json`
