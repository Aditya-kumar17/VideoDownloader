import flet as ft
import yt_dlp
import json
import os
import threading
from datetime import datetime

class FletVideoDownloader:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Video Downloader"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.padding = 20
        self.page.window_resizable = True
        
        # Initialize variables
        self.formats = []
        self.current_download_thread = None
        self.download_queue = []
        self.is_downloading = False
        self.history = []
        self.history_file = os.path.join(os.path.expanduser("~"), '.flet_video_downloader_history.json') # Safer path
        self.selected_format_index = None
        
        # Create UI
        self.setup_ui()
        self.load_history()
        self.refresh_history_list() # Initial population of history tab
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Create tabs
        self.tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="🎥 YouTube", content=self.create_youtube_tab()),
                ft.Tab(text="📷 Instagram", content=self.create_instagram_tab()),
                ft.Tab(text="📚 History", content=self.create_history_tab()),
                ft.Tab(text="⚙️ Settings", content=self.create_settings_tab()),
            ],
            expand=True,
        )
        
        # Status bar
        self.status_bar = ft.Text("Ready", size=14)
        
        # Main layout
        self.page.add(
            ft.Column(
                controls=[
                    self.tabs,
                    ft.Divider(),
                    self.status_bar
                ],
                expand=True,
            )
        )
    
    def create_youtube_tab(self):
        """Create YouTube download tab"""
        # URL input
        self.url_entry = ft.TextField(
            label="YouTube Video URL",
            hint_text="Enter YouTube video URL",
            expand=True,
            on_submit=self.fetch_formats
        )
        
        # Video info display
        self.video_title = ft.Text("No video selected", size=16, weight="bold")
        self.video_duration = ft.Text("", size=14)
        
        # Formats table
        self.formats_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Quality")),
                ft.DataColumn(ft.Text("Type")),
                ft.DataColumn(ft.Text("Size")),
                ft.DataColumn(ft.Text("FPS")),
                ft.DataColumn(ft.Text("Codecs")),
            ],
            rows=[],
        )
        
        # Download path
        self.download_path = ft.TextField(
            label="Download Location",
            value=os.path.join(os.path.expanduser("~"), "Downloads"),
            expand=True
        )
        
        # Progress
        self.progress_text = ft.Text("Ready to download")
        self.progress_bar = ft.ProgressBar(value=0, width=400)
        
        # Download button reference
        self.download_btn = ft.ElevatedButton(
            text="⬇️ Download Selected",
            on_click=self.download_selected,
            icon="DOWNLOAD",
            disabled=True
        )

        # FIX 1: Assign the "Fetch Formats" button to self.fetch_btn
        self.fetch_btn = ft.ElevatedButton(
            text="🔍 Fetch Formats",
            on_click=self.fetch_formats,
            icon="SEARCH"
        )
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.url_entry,
                        self.fetch_btn, # Use the instance attribute here
                        ft.ElevatedButton(
                            text="🗑️ Clear",
                            on_click=self.clear_youtube_form,
                            icon="DELETE",
                            color="error"
                        )
                    ]
                ),
                
                ft.Column(controls=[self.video_title, self.video_duration]),
                
                ft.Container(
                    content=ft.Column(
                    [self.formats_table],
                    scroll=ft.ScrollMode.ALWAYS
                    ),
                    height=200,
                    border=ft.border.all(1, color=ft.Colors.OUTLINE),
                    border_radius=ft.border_radius.all(5)
                        ),
                
                ft.Row(
                    controls=[
                        self.download_path,
                        ft.ElevatedButton(
                            text="📁 Browse",
                            on_click=self.browse_download_path,
                            icon="FOLDER_OPEN"
                        )
                    ]
                ),
                self.download_btn,
                
                self.progress_text,
                self.progress_bar
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    
    def create_instagram_tab(self):
        """Create Instagram download tab"""
        self.insta_entry = ft.TextField(
            label="Instagram Video URL",
            hint_text="Enter Instagram video or Reel URL",
            expand=True,
            on_submit=self.download_instagram
        )
        
        self.insta_info = ft.Text("Enter an Instagram video URL to download")
        
        self.insta_download_btn = ft.ElevatedButton(
            text="⬇️ Download Video",
            on_click=self.download_instagram,
            icon="DOWNLOAD"
        )
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.insta_entry,
                        self.insta_download_btn,
                        ft.ElevatedButton(
                            text="🗑️ Clear",
                            on_click=self.clear_instagram_form,
                            icon="DELETE",
                            color="error"
                        )
                    ]
                ),
                self.insta_info
            ]
        )
    
    def create_history_tab(self):
        """Create download history tab"""
        self.history_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Title")),
                ft.DataColumn(ft.Text("URL")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Platform")),
            ],
            rows=[]
        )
        
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="🔄 Refresh",
                            on_click=self.refresh_history_list,
                            icon="REFRESH"
                        ),
                        ft.ElevatedButton(
                            text="🗑️ Clear History",
                            on_click=self.clear_history,
                            icon="DELETE_FOREVER",
                            color="error"
                        )
                    ]
                ),
                ft.Container(
                    content=self.history_table,
                    height=400,
                    border=ft.border.all(1, color=ft.Colors.OUTLINE),
                    border_radius=ft.border_radius.all(5)
                )
            ]
        )
    
    def create_settings_tab(self):
        """Create settings tab"""
        self.theme_switch = ft.Switch(
            label="Dark Mode", 
            value=True,
            on_change=self.change_theme_mode
        )
        
        return ft.Column(
            controls=[
                ft.Text("General Settings", size=18, weight="bold"),
                self.theme_switch,
            ]
        )
    
    def update_status(self, message):
        """Update the status bar message"""
        self.status_bar.value = message
        self.page.update()

    def browse_download_path(self, e=None):
        """Placeholder for browsing download directory"""
        self.update_status("Feature not yet implemented. Please type the path manually.")

    # FIX 2: Add e=None to event handlers for consistency
    def clear_youtube_form(self, e=None):
        """Clear YouTube form fields"""
        self.url_entry.value = ""
        self.formats_table.rows.clear()
        self.video_title.value = "No video selected"
        self.video_duration.value = ""
        self.download_btn.disabled = True
        self.progress_bar.value = 0
        self.progress_text.value = "Ready to download"
        self.update_status("Form cleared")

    def clear_instagram_form(self, e=None):
        """Clear Instagram form fields"""
        self.insta_entry.value = ""
        self.insta_info.value = "Enter an Instagram video URL to download"
        self.update_status("Instagram form cleared")

    def change_theme_mode(self, e=None):
        """Change theme mode between dark and light"""
        self.page.theme_mode = ft.ThemeMode.DARK if self.theme_switch.value else ft.ThemeMode.LIGHT
        self.page.update()

    def fetch_formats(self, e=None):
        """Fetch available formats for a YouTube video"""
        url = self.url_entry.value.strip()
        if not url:
            self.update_status("Please enter a YouTube URL")
            return
        
        self.update_status("Fetching video formats...")
        self.fetch_btn.disabled = True
        self.page.update()
        
        thread = threading.Thread(target=self._fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _fetch_formats_thread(self, url):
        """Threaded function for fetching formats"""
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Update UI elements safely from the main thread
                self.page.run_thread(self._update_video_info, info)
                self.page.run_thread(self._populate_formats, info)
                self.page.run_thread(self.update_status, "Formats fetched successfully. Please select one.")
                
        except Exception as e:
            self.page.run_thread(self.update_status, f"Error fetching formats: {e}")
        finally:
            self.page.run_thread(lambda: setattr(self.fetch_btn, 'disabled', False))
            self.page.run_thread(self.page.update)
    
    def _update_video_info(self, info):
        """Update the video title and duration display"""
        title = info.get('title', 'Unknown Title')
        duration = info.get('duration', 0)
        
        self.video_title.value = title[:60] + "..." if len(title) > 60 else title
        
        if duration:
            mins, secs = divmod(duration, 60)
            self.video_duration.value = f"Duration: {mins:02d}:{secs:02d}"
        else:
            self.video_duration.value = "Duration: Unknown"
    
    def _populate_formats(self, info):
        """Populate the formats table with video/audio options"""
        self.formats_table.rows.clear()
        self.formats = [
            f for f in info.get('formats', [])
            if f.get('vcodec', 'none') != 'none' or f.get('acodec', 'none') != 'none'
        ]
        
        for i, f in enumerate(self.formats):
            height = f.get('height')
            quality = f"{height}p" if height else "Audio"
            
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            format_type = "Video+Audio" if vcodec != 'none' and acodec != 'none' else ("Video" if vcodec != 'none' else "Audio")
            
            filesize = f.get('filesize') or f.get('filesize_approx')
            size_str = f"{filesize / (1024*1024):.1f} MB" if filesize else "N/A"
            
            fps = f.get('fps')
            fps_str = str(fps) if fps else "N/A"
            
            codecs = f"{vcodec.split('.')[0]}/{acodec.split('.')[0]}" if vcodec != 'none' and acodec != 'none' else (vcodec.split('.')[0] if vcodec != 'none' else acodec.split('.')[0])
            
            self.formats_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(quality)),
                        ft.DataCell(ft.Text(format_type)),
                        ft.DataCell(ft.Text(size_str)),
                        ft.DataCell(ft.Text(fps_str)),
                        ft.DataCell(ft.Text(codecs)),
                    ],
                    on_select_changed=lambda e, index=i: self._select_format(index)
                )
            )
        self.download_btn.disabled = False if self.formats else True

    def _select_format(self, index):
        """Handle format selection from the table"""
        self.selected_format_index = index
        self.update_status(f"Selected format ID: {self.formats[index].get('format_id')}")
    
    def download_selected(self, e=None):
        """Download the format chosen by the user"""
        if self.selected_format_index is None:
            self.update_status("Please select a format to download.")
            return
        
        fmt = self.formats[self.selected_format_index]
        url = self.url_entry.value.strip()
        
        thread = threading.Thread(target=self._download_thread, args=(url, fmt))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url, fmt):
        """Threaded function for downloading YouTube video"""
        self.page.run_thread(lambda: setattr(self.download_btn, 'disabled', True))
        try:
            download_dir = self.download_path.value
            os.makedirs(download_dir, exist_ok=True)
            
            format_id = fmt.get('format_id')
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [self.ytdlp_progress_hook],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown Title')
                self.page.run_thread(self.update_status, "Download completed!")
                # FIX 3: Use 1.0 for progress bar completion
                self.page.run_thread(lambda: setattr(self.progress_bar, 'value', 1.0))
                self.page.run_thread(self.add_to_history, url, title, 'YouTube')
                
        except Exception as e:
            self.page.run_thread(self.update_status, f"Download failed: {e}")
        finally:
            self.is_downloading = False
            self.page.run_thread(lambda: setattr(self.download_btn, 'disabled', False))
            self.page.run_thread(self.page.update)
    
    def ytdlp_progress_hook(self, d):
        """Progress hook for yt-dlp to update the progress bar"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total_bytes:
                percent = d['downloaded_bytes'] / total_bytes
                speed = d.get('speed')
                speed_str = f"{speed / (1024*1024):.1f} MB/s" if speed else ""
                status_text = f"Downloading... {int(percent*100)}% ({speed_str})"
                self.page.run_thread(lambda: setattr(self.progress_bar, 'value', percent))
                self.page.run_thread(lambda: setattr(self.progress_text, 'value', status_text))
                self.page.run_thread(self.page.update)
        elif d['status'] == 'finished':
            self.page.run_thread(lambda: setattr(self.progress_text, 'value', "Processing... please wait."))
            self.page.run_thread(self.page.update)

    def download_instagram(self, e=None):
        """Download an Instagram video"""
        url = self.insta_entry.value.strip()
        if not url:
            self.update_status("Please enter an Instagram URL")
            return
        
        self.update_status("Starting Instagram download...")
        self.insta_download_btn.disabled = True
        self.page.update()
        
        thread = threading.Thread(target=self._download_instagram_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _download_instagram_thread(self, url):
        """Threaded function for downloading from Instagram"""
        try:
            download_dir = self.download_path.value
            os.makedirs(download_dir, exist_ok=True)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown Instagram Video')
                self.page.run_thread(self.update_status, "Instagram download completed!")
                self.page.run_thread(self.add_to_history, url, title, 'Instagram')
                
        except Exception as e:
            self.page.run_thread(self.update_status, f"Instagram download failed: {e}")
        finally:
            self.page.run_thread(lambda: setattr(self.insta_download_btn, 'disabled', False))
            self.page.run_thread(self.page.update)
    
    def add_to_history(self, url, title, platform):
        """Add a downloaded item to the history list and save it"""
        history_entry = {
            'url': url,
            'title': title,
            'platform': platform,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.history.insert(0, history_entry) # Add to the beginning
        self.save_history()
        self.refresh_history_list()
    
    def load_history(self):
        """Load download history from a JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Save the current download history to a JSON file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Failed to save history: {e}")
    
    def refresh_history_list(self, e=None):
        """Refresh the history table UI"""
        self.history_table.rows.clear()
        for entry in self.history:
            title = entry.get('title', 'Unknown')
            url = entry.get('url', '')
            
            self.history_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(title[:50] + "..." if len(title) > 50 else title)),
                        ft.DataCell(ft.Text(url[:40] + "..." if len(url) > 40 else url)),
                        ft.DataCell(ft.Text(entry.get('date', ''))),
                        ft.DataCell(ft.Text(entry.get('platform', 'N/A'))),
                    ]
                )
            )
        self.page.update()
    
    def clear_history(self, e=None):
        """Clear all entries from the download history"""
        if not self.history:
            self.update_status("History is already empty.")
            return
            
        self.history.clear()
        self.save_history()
        self.refresh_history_list()
        self.update_status("History cleared.")

def main(page: ft.Page):
    FletVideoDownloader(page)

if __name__ == "__main__":
    ft.app(target=main)
