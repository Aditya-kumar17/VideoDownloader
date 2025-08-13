import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import yt_dlp
import json
import os
from PIL import Image, ImageTk
import io
import urllib.request
import functools

class VideoDownloaderApp:
    def __init__(self, root=None):
        # Modern theme with dark mode option
        if root is None:
            self.root = tb.Window(themename="morph")  # Modern flat theme
        else:
            self.root = root
        self.root.title("Video Downloader Pro")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Create main style elements
        style = tb.Style()
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Card.TFrame', background=style.colors.get('secondary'))
        
        # Header frame
        header_frame = tb.Frame(self.root, bootstyle="dark")
        header_frame.pack(fill="x", pady=(0, 10))
        tb.Label(
            header_frame, 
            text="VIDEO DOWNLOADER PRO", 
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark"
        ).pack(pady=10)
        
        # Tab control
        self.tabs = tb.Notebook(self.root, bootstyle="dark")
        self.youtube_tab = tb.Frame(self.tabs)
        self.instagram_tab = tb.Frame(self.tabs)
        self.history_tab = tb.Frame(self.tabs)
        self.tabs.add(self.youtube_tab, text="YouTube")
        self.tabs.add(self.instagram_tab, text="Instagram")
        self.tabs.add(self.history_tab, text="History")
        self.tabs.pack(expand=1, fill="both", padx=10, pady=(0, 10))
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tb.Label(
            self.root, 
            textvariable=self.status_var, 
            relief="sunken", 
            anchor="w",
            bootstyle="info"
        )
        status_bar.pack(side="bottom", fill="x")
        
        # YouTube Tab UI - Modern Layout
        youtube_container = tb.Frame(self.youtube_tab)
        youtube_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Input Section
        input_frame = tb.LabelFrame(youtube_container, text="Video URL", bootstyle="info")
        input_frame.pack(fill="x", pady=(0, 15))
        
        tb.Label(input_frame, text="Enter YouTube URL:", bootstyle="info").pack(anchor="w", padx=5, pady=5)
        
        url_frame = tb.Frame(input_frame)
        url_frame.pack(fill="x", padx=5, pady=5)
        
        self.url_entry = tb.Entry(url_frame, bootstyle="info")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.fetch_btn = tb.Button(
            url_frame, 
            text="Fetch Formats", 
            command=self.fetch_formats, 
            bootstyle="outline-success",
            width=15
        )
        self.fetch_btn.pack(side="right")
        
        # Formats Section
        formats_frame = tb.LabelFrame(youtube_container, text="Available Formats", bootstyle="info")
        formats_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Create Treeview with scrollbar
        tree_frame = tb.Frame(formats_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("resolution", "type", "size", "codec")
        self.format_tree = tb.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            bootstyle="info",
            height=8
        )
        
        # Configure columns
        self.format_tree.heading("resolution", text="Resolution")
        self.format_tree.heading("type", text="Type")
        self.format_tree.heading("size", text="Size")
        self.format_tree.heading("codec", text="Codec")
        
        self.format_tree.column("resolution", width=100, anchor="center")
        self.format_tree.column("type", width=80, anchor="center")
        self.format_tree.column("size", width=100, anchor="center")
        self.format_tree.column("codec", width=150, anchor="center")
        
        # Add scrollbar
        scrollbar = tb.Scrollbar(tree_frame, orient="vertical", command=self.format_tree.yview)
        self.format_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.format_tree.pack(side="left", fill="both", expand=True)
        
        # Action Section
        action_frame = tb.Frame(youtube_container)
        action_frame.pack(fill="x", pady=(10, 0))
        
        self.download_btn = tb.Button(
            action_frame,
            text="Download Selected",
            command=self.download_selected,
            bootstyle="outline-danger",
            width=20,
            state="disabled"
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.progress = tb.Progressbar(
            action_frame,
            orient="horizontal",
            length=300,
            mode="determinate",
            bootstyle="info-striped"
        )
        self.progress.pack(side="left", fill="x", expand=True)
        
        # Instagram Tab UI
        insta_container = tb.Frame(self.instagram_tab)
        insta_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tb.Label(
            insta_container, 
            text="Instagram Video Download", 
            font=("Segoe UI", 12, "bold"),
            bootstyle="info"
        ).pack(pady=(0, 15))
        
        input_frame = tb.Frame(insta_container)
        input_frame.pack(fill="x", pady=5)
        
        tb.Label(input_frame, text="Enter Instagram URL:", bootstyle="info").pack(anchor="w")
        self.insta_entry = tb.Entry(input_frame, bootstyle="info")
        self.insta_entry.pack(fill="x", pady=5)
        
        self.insta_download_btn = tb.Button(
            insta_container,
            text="Download Video",
            command=self.download_instagram,
            bootstyle="success",
            width=15
        )
        self.insta_download_btn.pack(pady=15)
        
        # History Tab UI
        history_container = tb.Frame(self.history_tab)
        history_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tb.Label(
            history_container,
            text="Download History",
            font=("Segoe UI", 12, "bold"),
            bootstyle="info"
        ).pack(anchor="w", pady=(0, 10))
        
        # Create history treeview with scrollbar
        tree_frame = tb.Frame(history_container)
        tree_frame.pack(fill="both", expand=True)
        
        self.history_tree = tb.Treeview(
            tree_frame,
            columns=("title", "url", "platform"),
            show="headings",
            bootstyle="info",
            height=10
        )
        
        # Configure columns
        self.history_tree.heading("title", text="Title")
        self.history_tree.heading("url", text="URL")
        self.history_tree.heading("platform", text="Platform")
        
        self.history_tree.column("title", width=200, anchor="w")
        self.history_tree.column("url", width=300, anchor="w")
        self.history_tree.column("platform", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = tb.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.history_tree.pack(side="left", fill="both", expand=True)
        
        # Bind selection event
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)
        
        # History file and data
        self.history_file = os.path.join(os.path.dirname(__file__), 'history.json')
        self.history = self.load_history()
        self.refresh_history_list()
        
        # Initialize formats list
        self.formats = []
        
        # Set focus to URL entry
        self.url_entry.focus_set()

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def download_instagram(self):
        url = self.insta_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter an Instagram video URL.")
            return
        
        self.update_status("Downloading Instagram video...")
        self.insta_download_btn.config(state="disabled")
        
        try:
            ydl_opts = {
                'outtmpl': '%(title)s.%(ext)s',
                'quiet': True,
                'progress_hooks': [self.ytdlp_progress_hook],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            
            # Add to history
            title = info.get('title', url)
            thumbnail = info.get('thumbnail', '')
            if not any(h['url'] == url for h in self.history):
                self.history.append({
                    'url': url, 
                    'title': title, 
                    'thumbnail': thumbnail,
                    'platform': 'Instagram'
                })
                self.save_history()
                self.refresh_history_list()
            
            messagebox.showinfo("Success", "Instagram video downloaded successfully!")
            self.update_status("Instagram download complete")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download Instagram video: {str(e)}")
            self.update_status("Instagram download failed")
        finally:
            self.insta_download_btn.config(state="normal")

    def refresh_history_list(self):
        self.history_tree.delete(*self.history_tree.get_children())
        for idx, h in enumerate(self.history):
            self.history_tree.insert('', 'end', values=(
                h['title'][:60] + '...' if len(h['title']) > 60 else h['title'],
                h['url'][:50] + '...' if len(h['url']) > 50 else h['url'],
                h.get('platform', 'Unknown')
            ))

    def on_history_select(self, event):
        selected = self.history_tree.selection()
        if not selected:
            return
        item = self.history_tree.item(selected[0])
        url = self.history[self.history_tree.index(selected[0])]['url']
        
        # Set URL in YouTube tab
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        
        # Set URL in Instagram tab
        self.insta_entry.delete(0, tk.END)
        self.insta_entry.insert(0, url)
        
        # Switch to YouTube tab
        self.tabs.select(0)

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        
        self.update_status("Fetching video formats...")
        self.fetch_btn.config(state="disabled")
        self.format_tree.delete(*self.format_tree.get_children())
        self.formats = []
        
        try:
            ydl_opts = {
                'listformats': True, 
                'quiet': True,
                'extractor_args': {'youtube': {'skip': ['dash', 'hls']}}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Add to history
                title = info.get('title', url)
                thumbnail = info.get('thumbnail', '')
                if not any(h['url'] == url for h in self.history):
                    self.history.append({
                        'url': url, 
                        'title': title, 
                        'thumbnail': thumbnail,
                        'platform': 'YouTube'
                    })
                    self.save_history()
                    self.refresh_history_list()
                
                # Filter formats
                important_exts = {'mp4', 'm4a', 'webm'}
                for f in info.get('formats', []):
                    ext = f.get('ext', '')
                    if ext not in important_exts:
                        continue
                    
                    # Skip unsupported formats
                    format_note = f.get('format_note', '').lower()
                    if f.get('vcodec', '') == 'images' or 'storyboard' in format_note:
                        continue
                    
                    # Determine resolution
                    height = f.get('height')
                    if height is None:
                        res_str = 'Audio'
                    else:
                        resolutions = {
                            2160: '2160p (4K)',
                            1440: '1440p (QHD)',
                            1080: '1080p (HD)',
                            720: '720p (HD)',
                            480: '480p (SD)',
                            360: '360p',
                            240: '240p',
                            144: '144p'
                        }
                        res_str = resolutions.get(height, f'{height}p')
                    
                    # Calculate size
                    size = f.get('filesize') or f.get('filesize_approx')
                    size_str = f"{size/(1024*1024):.1f} MB" if size else 'N/A'
                    
                    # Format codec info
                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    codec_str = f"V: {vcodec.split('.')[0][:10]}, A: {acodec.split('.')[0][:10]}" 
                    
                    # Add to treeview
                    self.format_tree.insert('', 'end', values=(
                        res_str,
                        ext.upper(),
                        size_str,
                        codec_str
                    ))
                    self.formats.append(f)
            
            if not self.formats:
                messagebox.showinfo("Info", "No suitable formats found for this video")
                self.update_status("No formats found")
            else:
                self.download_btn.config(state="normal")
                self.update_status(f"Found {len(self.formats)} formats")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch formats: {str(e)}")
            self.update_status("Format fetch failed")
        finally:
            self.fetch_btn.config(state="normal")

    def download_selected(self):
        selection = self.format_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a format to download.")
            return
        
        idx = self.format_tree.index(selection[0])
        fmt = self.formats[idx]
        url = self.url_entry.get().strip()
        
        # Prepare download options
        format_id = fmt.get('format_id')
        height = fmt.get('height', 0)
        ext = fmt.get('ext', 'mp4')
        
        # Determine resolution string
        resolutions = {
            2160: '4K',
            1440: 'QHD',
            1080: 'HD1080',
            720: 'HD720',
            480: 'SD480',
            360: '360p',
            240: '240p',
            144: '144p'
        }
        res_str = resolutions.get(height, 'Audio')
        
        ydl_opts = {
            'format': format_id,
            'outtmpl': f'%(title)s_{res_str}.{ext}',
            'progress_hooks': [self.ytdlp_progress_hook],
            'merge_output_format': ext if ext in ['mp4', 'm4a'] else 'mp4',
        }
        
        self.progress['value'] = 0
        self.download_btn.config(state="disabled")
        self.update_status(f"Downloading {res_str} format...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Success", "Download completed successfully!")
            self.update_status("Download complete")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")
            self.update_status("Download failed")
        finally:
            self.progress['value'] = 0
            self.download_btn.config(state="normal")

    def ytdlp_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = min(100, int(downloaded / total_bytes * 100))
                self.progress['value'] = percent
                self.update_status(f"Downloading: {percent}%")
        elif d['status'] == 'finished':
            self.progress['value'] = 100
            self.update_status("Finalizing download...")

def main():
    app = VideoDownloaderApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()