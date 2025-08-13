# Modern Video Downloader Pro v3.0

A professional and modern video downloader application built with Python and ttkbootstrap. This application provides a sleek, user-friendly interface for downloading videos from YouTube and Instagram.

## ✨ Features

### 🎥 YouTube Download
- **Multiple Format Support**: Download videos in various resolutions (4K, 2K, Full HD, HD, SD)
- **Format Selection**: Choose from video-only, audio-only, or video+audio formats
- **Quality Information**: View file size, FPS, and codec information for each format
- **Smart Format Detection**: Automatically handles video-only formats by adding best audio

### 📷 Instagram Download
- **Simple Interface**: One-click download for Instagram videos
- **Automatic Format Detection**: Automatically selects the best available format

### 📚 Download History
- **Comprehensive History**: Track all downloads with timestamps and platform information
- **Quick Re-download**: Double-click any history item to re-download
- **History Management**: Clear individual entries or entire history

### ⚙️ Settings & Customization
- **Multiple Themes**: Choose from 8 different modern themes
- **Download Path**: Customizable download directory with browse functionality
- **Auto-folder Creation**: Automatically create download folders
- **Notifications**: Toggle download completion notifications

### 🎨 Modern UI
- **Professional Design**: Clean, modern interface with ttkbootstrap
- **Responsive Layout**: Adapts to different window sizes
- **Status Bar**: Real-time download progress and status updates
- **Progress Tracking**: Visual progress bar with download speed information

## 🚀 Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd VideoDownloader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python downloader3.py
   ```

## 📋 Requirements

- Python 3.7 or higher
- ttkbootstrap >= 1.10.1
- yt-dlp >= 2023.12.30
- Pillow >= 10.0.0

## 🎯 Usage

### YouTube Downloads
1. Navigate to the **YouTube** tab
2. Paste a YouTube video URL
3. Click **"Fetch Formats"** to see available options
4. Select your preferred format from the list
5. Choose download location (optional)
6. Click **"Download Selected"**

### Instagram Downloads
1. Navigate to the **Instagram** tab
2. Paste an Instagram video URL
3. Click **"Download Video"**

### History Management
- View all downloads in the **History** tab
- Double-click any entry to re-download
- Use **"Clear History"** to remove all entries

### Settings
- **Theme Selection**: Choose from 8 different themes
- **Download Path**: Set default download directory
- **Auto-create Folders**: Automatically create download folders
- **Notifications**: Toggle download completion alerts

## 🎨 Available Themes

- **darkly** - Dark theme with blue accents
- **superhero** - Dark theme with purple accents
- **cyborg** - Dark theme with green accents
- **solar** - Light theme with orange accents
- **flatly** - Light theme with blue accents
- **journal** - Light theme with gray accents
- **cosmo** - Light theme with purple accents
- **vapor** - Light theme with pink accents

## 🔧 Technical Details

### Architecture
- **Threading**: All downloads run in separate threads to prevent UI freezing
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Progress Tracking**: Real-time progress updates with download speed
- **File Management**: Automatic file naming with resolution indicators

### File Structure
```
VideoDownloader/
├── downloader3.py          # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── history.json           # Download history (auto-generated)
└── downloads/             # Default download directory (auto-created)
```

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'ttkbootstrap'"**
   - Solution: Run `pip install ttkbootstrap`

2. **"No module named 'yt_dlp'"**
   - Solution: Run `pip install yt-dlp`

3. **Download fails with "Video unavailable"**
   - Solution: Check if the video is available in your region
   - Try updating yt-dlp: `pip install --upgrade yt-dlp`

4. **Slow download speeds**
   - Solution: Check your internet connection
   - Try selecting a lower quality format

### Performance Tips

- Use wired internet connection for faster downloads
- Close other bandwidth-intensive applications
- Select appropriate quality based on your needs

## 📝 Changelog

### v3.0 (Current)
- Complete UI redesign with ttkbootstrap
- Added multiple themes support
- Enhanced format selection with detailed information
- Improved download progress tracking
- Added comprehensive settings panel
- Better error handling and user feedback
- Threading for non-blocking downloads
- Professional status bar and notifications

### Previous Versions
- v2.0: Added Instagram support and improved YouTube functionality
- v1.0: Basic YouTube downloader

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📄 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

This application is for personal use only. Please respect copyright laws and terms of service of the platforms you download from. The developers are not responsible for any misuse of this software.

---

**Made with ❤️ using Python and ttkbootstrap**
