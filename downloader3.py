import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import yt_dlp
import json
import os
import threading
from PIL import Image, ImageTk
import io
import urllib.request
import functools
import time
from datetime import datetime
import re

class ModernVideoDownloader:
    def __init__(self):
        # Initialize the main window with a modern theme
        self.root = tb.Window(themename="darkly")
        self.root.title("Video Downloader")
        self.root.geometry("900x700")
        self.root.minsize(800, 1000)
        
        # Configure grid weights for responsive layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Initialize variables
        self.formats = []
        self.current_download_thread = None
        self.download_queue = []
        self.is_downloading = False
        
        # Setup UI
        self.setup_ui()
        self.load_history()
        
        # Center window on screen
        self.center_window()
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup the main UI components"""
        # Main container
        main_frame = tb.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        self.create_header(main_frame)
        
        # Notebook for tabs
        self.notebook = tb.Notebook(main_frame, bootstyle="primary")
        self.notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        # Create tabs
        self.create_youtube_tab()
        self.create_instagram_tab()
        self.create_history_tab()
        self.create_settings_tab()
        
        # Status bar
        self.create_status_bar(main_frame)
    
    def create_header(self, parent):
        """Create the header section"""
        header_frame = tb.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)
    
    def create_youtube_tab(self):
        """Create the YouTube download tab"""
        youtube_frame = tb.Frame(self.notebook)
        self.notebook.add(youtube_frame, text="🎥 YouTube")
        
        # URL input section
        url_frame = tb.LabelFrame(youtube_frame, text="Video URL", padding=15)
        url_frame.pack(fill="x", padx=10, pady=10)
        
        self.url_entry = tb.Entry(url_frame, font=("Segoe UI", 11), bootstyle="info")
        self.url_entry.pack(fill="x", pady=(0, 10))
        self.url_entry.bind('<Return>', lambda e: self.fetch_formats())
        
        # Buttons frame
        btn_frame = tb.Frame(url_frame)
        btn_frame.pack(fill="x")
        
        self.fetch_btn = tb.Button(btn_frame, text="🔍 Fetch Formats", 
                                 command=self.fetch_formats, bootstyle="success-outline")
        self.fetch_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = tb.Button(btn_frame, text="🗑️ Clear", 
                                 command=self.clear_youtube_form, bootstyle="danger-outline")
        self.clear_btn.pack(side="left")
        
        # Video info section
        self.info_frame = tb.LabelFrame(youtube_frame, text="Video Information", padding=15)
        self.info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.video_title_label = tb.Label(self.info_frame, text="No video selected", 
                                        font=("Segoe UI", 12, "bold"))
        self.video_title_label.pack(anchor="w")
        
        self.video_duration_label = tb.Label(self.info_frame, text="", 
                                           font=("Segoe UI", 10))
        self.video_duration_label.pack(anchor="w")
        
        # Formats section
        formats_frame = tb.LabelFrame(youtube_frame, text="Available Formats", padding=15)
        formats_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create Treeview for formats
        columns = ('Quality', 'Format', 'Size', 'FPS', 'Codec')
        self.formats_tree = ttk.Treeview(formats_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        for col in columns:
            self.formats_tree.heading(col, text=col)
            self.formats_tree.column(col, width=100, anchor="center")
        
        # Scrollbar for formats
        formats_scrollbar = ttk.Scrollbar(formats_frame, orient="vertical", command=self.formats_tree.yview)
        self.formats_tree.configure(yscrollcommand=formats_scrollbar.set)
        
        self.formats_tree.pack(side="left", fill="both", expand=True)
        formats_scrollbar.pack(side="right", fill="y")
        
        # Download section
        download_frame = tb.LabelFrame(youtube_frame, text="Download", padding=15)
        download_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Download options
        options_frame = tb.Frame(download_frame)
        options_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(options_frame, text="Download Location:").pack(side="left")
        self.download_path = tk.StringVar(value=os.path.join(os.getcwd(), "downloads"))
        self.path_entry = tb.Entry(options_frame, textvariable=self.download_path, width=40)
        self.path_entry.pack(side="left", padx=(10, 5))
        
        self.browse_btn = tb.Button(options_frame, text="📁 Browse", 
                                  command=self.browse_download_path, bootstyle="info-outline")
        self.browse_btn.pack(side="left")
        
        # Download button
        self.download_btn = tb.Button(download_frame, text="⬇️ Download Selected", 
                                    command=self.download_selected, bootstyle="success", 
                                    state="disabled")
        self.download_btn.pack(pady=(10, 0))
        
        # Progress section
        progress_frame = tb.Frame(download_frame)
        progress_frame.pack(fill="x", pady=(10, 0))
        
        self.progress_label = tb.Label(progress_frame, text="Ready to download")
        self.progress_label.pack(anchor="w")
        
        self.progress_bar = tb.Progressbar(progress_frame, orient="horizontal", 
                                         length=400, mode="determinate", bootstyle="success")
        self.progress_bar.pack(fill="x", pady=(5, 0))
    
    def create_instagram_tab(self):
        """Create the Instagram download tab"""
        instagram_frame = tb.Frame(self.notebook)
        self.notebook.add(instagram_frame, text="📷 Instagram")
        
        # URL input section
        url_frame = tb.LabelFrame(instagram_frame, text="Instagram Video URL", padding=15)
        url_frame.pack(fill="x", padx=10, pady=10)
        
        self.insta_entry = tb.Entry(url_frame, font=("Segoe UI", 11), bootstyle="info")
        self.insta_entry.pack(fill="x", pady=(0, 10))
        self.insta_entry.bind('<Return>', lambda e: self.download_instagram())
        
        # Buttons
        btn_frame = tb.Frame(url_frame)
        btn_frame.pack(fill="x")
        
        self.insta_download_btn = tb.Button(btn_frame, text="⬇️ Download Video", 
                                          command=self.download_instagram, bootstyle="success")
        self.insta_download_btn.pack(side="left", padx=(0, 10))
        
        self.insta_clear_btn = tb.Button(btn_frame, text="🗑️ Clear", 
                                       command=self.clear_instagram_form, bootstyle="danger-outline")
        self.insta_clear_btn.pack(side="left")
        
        # Info section
        self.insta_info_frame = tb.LabelFrame(instagram_frame, text="Information", padding=15)
        self.insta_info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.insta_info_label = tb.Label(self.insta_info_frame, 
                                       text="Enter an Instagram video URL to download")
        self.insta_info_label.pack()
    
    def create_history_tab(self):
        """Create the download history tab"""
        history_frame = tb.Frame(self.notebook)
        self.notebook.add(history_frame, text="📚 History")
        
        # History controls
        controls_frame = tb.Frame(history_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        self.refresh_history_btn = tb.Button(controls_frame, text="🔄 Refresh", 
                                           command=self.refresh_history_list, bootstyle="info-outline")
        self.refresh_history_btn.pack(side="left", padx=(0, 10))
        
        self.clear_history_btn = tb.Button(controls_frame, text="🗑️ Clear History", 
                                         command=self.clear_history, bootstyle="danger-outline")
        self.clear_history_btn.pack(side="left")
        
        # History list
        history_list_frame = tb.LabelFrame(history_frame, text="Download History", padding=15)
        history_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create Treeview for history
        columns = ('Title', 'URL', 'Date', 'Platform')
        self.history_tree = ttk.Treeview(history_list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            if col == 'Title':
                self.history_tree.column(col, width=300, anchor="w")
            elif col == 'URL':
                self.history_tree.column(col, width=200, anchor="w")
            else:
                self.history_tree.column(col, width=100, anchor="center")
        
        # Scrollbar
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        
        # Bind double-click event
        self.history_tree.bind('<Double-1>', self.on_history_double_click)
        
        # History file path
        self.history_file = os.path.join(os.path.dirname(__file__), 'history.json')
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = tb.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # General settings
        general_frame = tb.LabelFrame(settings_frame, text="General Settings", padding=15)
        general_frame.pack(fill="x", padx=10, pady=10)
        
        # Default download path
        path_frame = tb.Frame(general_frame)
        path_frame.pack(fill="x", pady=(0, 10))
        
        tb.Label(path_frame, text="Default Download Path:").pack(anchor="w")
        self.default_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "downloads"))
        default_path_entry = tb.Entry(path_frame, textvariable=self.default_path_var, width=50)
        default_path_entry.pack(fill="x", pady=(5, 0))
        
        # Theme selection
        theme_frame = tb.Frame(general_frame)
        theme_frame.pack(fill="x", pady=(10, 0))
        
        tb.Label(theme_frame, text="Theme:").pack(anchor="w")
        self.theme_var = tk.StringVar(value="darkly")
        themes = ["darkly", "superhero", "cyborg", "solar", "flatly", "journal", "cosmo", "vapor"]
        theme_combo = tb.Combobox(theme_frame, textvariable=self.theme_var, values=themes, state="readonly")
        theme_combo.pack(fill="x", pady=(5, 0))
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        
        # Download settings
        download_settings_frame = tb.LabelFrame(settings_frame, text="Download Settings", padding=15)
        download_settings_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Auto-create folders
        self.auto_create_folders = tk.BooleanVar(value=True)
        auto_folder_check = tb.Checkbutton(download_settings_frame, text="Auto-create download folders", 
                                         variable=self.auto_create_folders, bootstyle="round-toggle")
        auto_folder_check.pack(anchor="w", pady=(0, 5))
        
        # Show download notifications
        self.show_notifications = tk.BooleanVar(value=True)
        notifications_check = tb.Checkbutton(download_settings_frame, text="Show download notifications", 
                                           variable=self.show_notifications, bootstyle="round-toggle")
        notifications_check.pack(anchor="w")
    
    def create_status_bar(self, parent):
        """Create the status bar"""
        self.status_bar = tb.Label(parent, text="Ready", relief="sunken", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    
    def update_status(self, message):
        """Update the status bar message"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def browse_download_path(self):
        """Browse for download directory"""
        path = filedialog.askdirectory(initialdir=self.download_path.get())
        if path:
            self.download_path.set(path)
    
    def clear_youtube_form(self):
        """Clear YouTube form fields"""
        self.url_entry.delete(0, tk.END)
        self.formats_tree.delete(*self.formats_tree.get_children())
        self.video_title_label.config(text="No video selected")
        self.video_duration_label.config(text="")
        self.download_btn.config(state="disabled")
        self.update_status("Form cleared")
    
    def clear_instagram_form(self):
        """Clear Instagram form fields"""
        self.insta_entry.delete(0, tk.END)
        self.insta_info_label.config(text="Enter an Instagram video URL to download")
        self.update_status("Instagram form cleared")
    
    def change_theme(self, event=None):
        """Change the application theme"""
        theme = self.theme_var.get()
        self.root.style.theme_use(theme)
        self.update_status(f"Theme changed to {theme}")
    
    def fetch_formats(self):
        """Fetch available formats for YouTube video"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        
        self.update_status("Fetching video formats...")
        self.fetch_btn.config(state="disabled")
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._fetch_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _fetch_formats_thread(self, url):
        """Thread function for fetching formats"""
        try:
            ydl_opts = {
                'listformats': True,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Update UI in main thread
                self.root.after(0, lambda: self._update_video_info(info))
                self.root.after(0, lambda: self._populate_formats(info))
                self.root.after(0, lambda: self.update_status("Formats fetched successfully"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch formats: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Failed to fetch formats"))
        finally:
            self.root.after(0, lambda: self.fetch_btn.config(state="normal"))
    
    def _update_video_info(self, info):
        """Update video information display"""
        title = info.get('title', 'Unknown Title')
        duration = info.get('duration', 0)
        
        # Truncate long titles
        if len(title) > 60:
            title = title[:57] + "..."
        
        self.video_title_label.config(text=title)
        
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            duration_str = f"Duration: {minutes}:{seconds:02d}"
        else:
            duration_str = "Duration: Unknown"
        
        self.video_duration_label.config(text=duration_str)
    
    def _populate_formats(self, info):
        """Populate the formats treeview"""
        self.formats_tree.delete(*self.formats_tree.get_children())
        self.formats = []
        
        important_exts = {'mp4', 'm4a', 'webm'}
        
        for f in info.get('formats', []):
            ext = f.get('ext', '')
            if ext not in important_exts:
                continue
            
            # Skip storyboards and images
            format_note = f.get('format_note', '').lower()
            if f.get('vcodec', '') == 'images' or 'storyboard' in format_note:
                continue
            
            height = f.get('height')
            filesize = f.get('filesize')
            fps = f.get('fps')
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            
            # Determine quality string
            if height is None:
                quality = 'Audio Only'
            elif height >= 2160:
                quality = '4K (2160p)'
            elif height >= 1440:
                quality = '2K (1440p)'
            elif height >= 1080:
                quality = 'Full HD (1080p)'
            elif height >= 720:
                quality = 'HD (720p)'
            elif height >= 480:
                quality = 'SD (480p)'
            else:
                quality = f'{height}p'
            
            # Format string
            if vcodec != 'none' and acodec != 'none':
                format_type = 'Video + Audio'
            elif vcodec != 'none':
                format_type = 'Video Only'
            else:
                format_type = 'Audio Only'
            
            # Size string
            if filesize:
                size_mb = filesize / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "Unknown"
            
            # FPS string
            fps_str = f"{fps}" if fps else "N/A"
            
            # Codec string
            codec_str = f"{vcodec}/{acodec}" if vcodec != 'none' and acodec != 'none' else (vcodec if vcodec != 'none' else acodec)
            
            # Insert into treeview
            item = self.formats_tree.insert('', 'end', values=(quality, format_type, size_str, fps_str, codec_str))
            self.formats.append(f)
        
        self.download_btn.config(state="normal")
    
    def download_selected(self):
        """Download the selected format"""
        selection = self.formats_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a format to download.")
            return
        
        # Get selected format
        selected_item = selection[0]
        format_index = self.formats_tree.index(selected_item)
        fmt = self.formats[format_index]
        
        url = self.url_entry.get().strip()
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_thread, args=(url, fmt))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, url, fmt):
        """Thread function for downloading"""
        try:
            self.is_downloading = True
            self.root.after(0, lambda: self.download_btn.config(state="disabled"))
            self.root.after(0, lambda: self.update_status("Starting download..."))
            
            # Ensure download directory exists
            download_dir = self.download_path.get()
            if self.auto_create_folders.get():
                os.makedirs(download_dir, exist_ok=True)
            
            # Prepare download options
            format_id = fmt.get('format_id')
            height = fmt.get('height')
            
            # Determine resolution string for filename
            if height is None:
                res_str = 'audio'
            elif height >= 2160:
                res_str = '2160p'
            elif height >= 1440:
                res_str = '1440p'
            elif height >= 1080:
                res_str = '1080p'
            elif height >= 720:
                res_str = '720p'
            elif height >= 480:
                res_str = '480p'
            else:
                res_str = f'{height}p'
            
            ext = fmt.get('ext', 'mp4')
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(download_dir, f'%(title)s_{res_str}.{ext}'),
                'merge_output_format': ext if ext in ['mp4', 'm4a'] else 'mp4',
                'progress_hooks': [self.ytdlp_progress_hook],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Add to history
                title = info.get('title', url)
                self.add_to_history(url, title, 'YouTube')
                
                self.root.after(0, lambda: self.progress_bar.config(value=100))
                self.root.after(0, lambda: self.update_status("Download completed!"))
                
                if self.show_notifications.get():
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Download failed"))
        finally:
            self.is_downloading = False
            self.root.after(0, lambda: self.download_btn.config(state="normal"))
            self.root.after(0, lambda: self.progress_bar.config(value=0))
    
    def ytdlp_progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            
            if total_bytes:
                percent = int(downloaded / total_bytes * 100)
                self.root.after(0, lambda p=percent: self.progress_bar.config(value=p))
                
                # Update status with download speed
                speed = d.get('speed')
                if speed:
                    speed_mb = speed / (1024 * 1024)
                    status_text = f"Downloading... {percent}% ({speed_mb:.1f} MB/s)"
                else:
                    status_text = f"Downloading... {percent}%"
                
                self.root.after(0, lambda: self.update_status(status_text))
        
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_bar.config(value=100))
            self.root.after(0, lambda: self.update_status("Processing..."))
    
    def download_instagram(self):
        """Download Instagram video"""
        url = self.insta_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter an Instagram video URL.")
            return
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_instagram_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _download_instagram_thread(self, url):
        """Thread function for Instagram download"""
        try:
            self.root.after(0, lambda: self.insta_download_btn.config(state="disabled"))
            self.root.after(0, lambda: self.update_status("Downloading Instagram video..."))
            
            # Ensure download directory exists
            download_dir = self.download_path.get()
            if self.auto_create_folders.get():
                os.makedirs(download_dir, exist_ok=True)
            
            ydl_opts = {
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Add to history
                title = info.get('title', url)
                self.add_to_history(url, title, 'Instagram')
                
                self.root.after(0, lambda: self.update_status("Instagram download completed!"))
                
                if self.show_notifications.get():
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Instagram video downloaded successfully!"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to download Instagram video: {str(e)}"))
            self.root.after(0, lambda: self.update_status("Instagram download failed"))
        finally:
            self.root.after(0, lambda: self.insta_download_btn.config(state="normal"))
    
    def add_to_history(self, url, title, platform):
        """Add download to history"""
        history_entry = {
            'url': url,
            'title': title,
            'platform': platform,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.history.append(history_entry)
        self.save_history()
        self.refresh_history_list()
    
    def load_history(self):
        """Load download history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        """Save download history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")
    
    def refresh_history_list(self):
        """Refresh the history list display"""
        self.history_tree.delete(*self.history_tree.get_children())
        
        for entry in reversed(self.history):  # Show newest first
            title = entry.get('title', 'Unknown')
            url = entry.get('url', '')
            date = entry.get('date', '')
            platform = entry.get('platform', 'Unknown')
            
            # Truncate long titles
            if len(title) > 50:
                title = title[:47] + "..."
            
            self.history_tree.insert('', 'end', values=(title, url, date, platform))
    
    def on_history_double_click(self, event):
        """Handle double-click on history item"""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.history_tree.item(item, 'values')
        url = values[1]  # URL is in second column
        
        # Switch to appropriate tab and set URL
        platform = values[3]  # Platform is in fourth column
        
        if platform.lower() == 'youtube':
            self.notebook.select(0)  # YouTube tab
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        elif platform.lower() == 'instagram':
            self.notebook.select(1)  # Instagram tab
            self.insta_entry.delete(0, tk.END)
            self.insta_entry.insert(0, url)
    
    def clear_history(self):
        """Clear download history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all download history?"):
            self.history = []
            self.save_history()
            self.refresh_history_list()
            self.update_status("History cleared")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    app = ModernVideoDownloader()
    app.run()

if __name__ == "__main__":
    main()
