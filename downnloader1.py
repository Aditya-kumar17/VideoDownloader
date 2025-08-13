import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import yt_dlp
import json
import os
from PIL import Image, ImageTk
import io
import urllib.request
import threading
import queue

class SettingsManager:
    """Manages loading and saving application settings from a JSON file."""
    def __init__(self, filepath='settings.json'):
        self.filepath = filepath
        self.settings = self.load_settings()

    def load_settings(self):
        """Loads settings from the JSON file, or returns defaults if it doesn't exist."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Ensure all default keys exist
                defaults = self.get_default_settings()
                for key, value in defaults.items():
                    settings.setdefault(key, value)
                return settings
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_settings()

    def get_default_settings(self):
        """Returns a dictionary of default settings."""
        return {
            "theme": "superhero",
            "download_path": os.path.join(os.path.expanduser('~'), 'Downloads'),
            "history": []
        }

    def save_settings(self):
        """Saves the current settings to the JSON file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, key, default=None):
        """Gets a specific setting value."""
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        """Updates a setting and saves it."""
        self.settings[key] = value
        self.save_settings()

class DownloaderFrame(ttk.Frame):
    """Frame for the main downloader UI (YouTube, Instagram, etc.)."""
    def __init__(self, parent, settings_manager, update_status_callback, update_history_callback):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.update_status = update_status_callback
        self.update_history = update_history_callback

        self.formats = []
        self.info = {}
        self.is_downloading = False
        self.progress_queue = queue.Queue()

        self.create_widgets()
        self.check_progress_queue()

    def create_widgets(self):
        """Create and grid the widgets for the downloader."""
        # --- URL Input ---
        url_frame = ttk.Frame(self)
        url_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        url_frame.columnconfigure(1, weight=1)

        url_label = ttk.Label(url_frame, text="Video URL:")
        url_label.grid(row=0, column=0, padx=(0, 5))
        self.url_entry = ttk.Entry(url_frame, bootstyle="info")
        self.url_entry.grid(row=0, column=1, sticky="ew")

        self.fetch_btn = ttk.Button(url_frame, text="Fetch Formats", command=self.start_fetch_formats, bootstyle="primary")
        self.fetch_btn.grid(row=0, column=2, padx=(5, 0))

        # --- Format List ---
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.format_list = tk.Listbox(list_frame, width=80, height=10, relief="flat")
        self.format_list.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.format_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.format_list.config(yscrollcommand=scrollbar.set)

        # --- Download Controls ---
        download_frame = ttk.Frame(self)
        download_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        download_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(download_frame, orient="horizontal", mode="determinate", bootstyle="info")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.download_btn = ttk.Button(download_frame, text="Download Selected", command=self.start_download, bootstyle="success-outline")
        self.download_btn.grid(row=0, column=1)

        # --- Configure Grid Weights ---
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def start_fetch_formats(self):
        """Starts the format fetching process in a background thread."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return
        if self.is_downloading:
            messagebox.showwarning("Busy", "A download is already in progress.")
            return

        self.toggle_controls(False)
        self.update_status("Fetching formats...")
        thread = threading.Thread(target=self._execute_fetch_formats, args=(url,))
        thread.daemon = True
        thread.start()

    def _execute_fetch_formats(self, url):
        """The actual format fetching logic that runs in the background."""
        try:
            ydl_opts = {'listformats': True, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.info = ydl.extract_info(url, download=False)

            self.formats = []
            display_formats = []
            important_exts = {'mp4', 'm4a', 'webm'}

            for f in self.info.get('formats', []):
                ext = f.get('ext', '')
                if ext not in important_exts:
                    continue

                format_note = f.get('format_note', '').lower()
                vcodec = f.get('vcodec', 'none')
                if vcodec == 'none':
                    res_str = f"Audio Only ({f.get('acodec', 'N/A')})"
                    filesize_str = f" | Size: {f.get('filesize_approx_str', 'N/A')}"
                else:
                    height = f.get('height')
                    res_str = f"{height}p" if height else "Video"
                    filesize_str = f" | Size: {f.get('filesize_approx_str', 'N/A')}"
                
                fmt_str = f"Res: {res_str:<18} | Type: {ext:<5} {filesize_str}"
                display_formats.append(fmt_str)
                self.formats.append(f)

            self.progress_queue.put(('formats_ready', display_formats))
        except Exception as e:
            self.progress_queue.put(('error', f"Failed to fetch formats: {e}"))

    def start_download(self):
        """Starts the download process in a background thread."""
        selection = self.format_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a format to download.")
            return
        if self.is_downloading:
            messagebox.showwarning("Busy", "A download is already in progress.")
            return

        fmt = self.formats[selection[0]]
        url = self.url_entry.get().strip()
        
        self.toggle_controls(False)
        self.is_downloading = True
        self.progress['value'] = 0
        self.progress.config(bootstyle="info")

        thread = threading.Thread(target=self._execute_download, args=(url, fmt))
        thread.daemon = True
        thread.start()
        
    def _execute_download(self, url, fmt):
        """The actual download logic that runs in the background."""
        try:
            format_id = fmt['format_id']
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')

            # If the selected format is video-only, find the best audio to merge
            if vcodec != 'none' and acodec == 'none':
                format_selector = f"{format_id}+bestaudio/best"
            else:
                format_selector = format_id

            download_path = self.settings_manager.get_setting('download_path')
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(download_path, '%(title)s - %(resolution)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [self.ytdlp_progress_hook],
                'quiet': True,
                'noprogress': True, # Disable console progress bar
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as e:
            self.progress_queue.put(('error', f"Download failed: {e}"))

    def ytdlp_progress_hook(self, d):
        """Progress hook for yt-dlp, sends data to the main thread via queue."""
        self.progress_queue.put(('progress', d))

    def check_progress_queue(self):
        """Periodically checks the queue for updates from the background thread."""
        try:
            while True:
                message_type, data = self.progress_queue.get_nowait()
                self.handle_queue_message(message_type, data)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_progress_queue)

    def handle_queue_message(self, message_type, data):
        """Processes messages from the queue on the main UI thread."""
        if message_type == 'progress':
            if data['status'] == 'downloading':
                total = data.get('total_bytes') or data.get('total_bytes_estimate')
                if total:
                    percent = (data['downloaded_bytes'] / total) * 100
                    self.progress['value'] = percent
                    speed = data.get('speed_str', 'N/A')
                    eta = data.get('eta_str', 'N/A')
                    self.update_status(f"Downloading... {percent:.1f}% at {speed} (ETA: {eta})")
            elif data['status'] == 'finished':
                self.progress['value'] = 100
                self.progress.config(bootstyle="success")
                self.update_status(f"Download finished: {os.path.basename(data['filename'])}")
                self.is_downloading = False
                self.toggle_controls(True)
                self.add_to_history()
        elif message_type == 'formats_ready':
            self.format_list.delete(0, tk.END)
            for fmt_str in data:
                self.format_list.insert(tk.END, fmt_str)
            self.update_status(f"Found {len(data)} formats for '{self.info.get('title', 'video')}'.")
            self.toggle_controls(True)
        elif message_type == 'error':
            messagebox.showerror("Error", str(data))
            self.update_status("Error occurred.", "danger")
            self.progress.config(bootstyle="danger")
            self.is_downloading = False
            self.toggle_controls(True)

    def toggle_controls(self, is_enabled):
        """Enable or disable UI controls."""
        state = "normal" if is_enabled else "disabled"
        self.fetch_btn.config(state=state)
        self.download_btn.config(state=state)
        self.url_entry.config(state=state)

    def add_to_history(self):
        """Adds the downloaded video to history and saves it."""
        url = self.info.get('webpage_url', self.url_entry.get().strip())
        title = self.info.get('title', 'Unknown Title')
        thumbnail = self.info.get('thumbnail', '')
        
        history = self.settings_manager.get_setting('history', [])
        # Avoid duplicates
        if not any(h['url'] == url for h in history):
            history.insert(0, {'url': url, 'title': title, 'thumbnail': thumbnail})
            self.settings_manager.update_setting('history', history)
            self.update_history()

class HistoryFrame(ttk.Frame):
    """Frame for displaying download history."""
    def __init__(self, parent, settings_manager, url_setter_callback):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.set_url_in_downloader = url_setter_callback
        self.thumbnail_cache = {}
        self.photo_images = []  # To prevent garbage collection

        self.create_widgets()
        self.load_history()

    def create_widgets(self):
        """Create and grid the widgets for the history view."""
        # --- Search Bar ---
        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        search_frame.columnconfigure(1, weight=1)
        
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_history)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # --- Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=("Title", "URL"), show="headings", selectmode="browse")
        self.tree.heading("Title", text="Title")
        self.tree.heading("URL", text="URL")
        self.tree.column("Title", width=300)
        self.tree.column("URL", width=200)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_history_select)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=scrollbar.set)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def load_history(self):
        """Loads history from settings and populates the treeview."""
        self.tree.delete(*self.tree.get_children())
        self.photo_images.clear()
        history = self.settings_manager.get_setting('history', [])
        for item in history:
            # Insert item without image first
            self.tree.insert("", "end", values=(item['title'], item['url']), iid=item['url'])
            # Load thumbnail in background
            self.load_thumbnail(item['url'], item['thumbnail'])

    def load_thumbnail(self, url_id, thumb_url):
        """Loads a single thumbnail in a background thread."""
        if not thumb_url:
            return
        if thumb_url in self.thumbnail_cache:
            self.tree.item(url_id, image=self.thumbnail_cache[thumb_url])
            return
        
        thread = threading.Thread(target=self._execute_load_thumbnail, args=(url_id, thumb_url))
        thread.daemon = True
        thread.start()

    def _execute_load_thumbnail(self, url_id, thumb_url):
        """Fetches and processes a thumbnail image."""
        try:
            with urllib.request.urlopen(thumb_url) as u:
                raw_data = u.read()
            img = Image.open(io.BytesIO(raw_data)).resize((64, 36), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.photo_images.append(photo) # Keep reference
            self.thumbnail_cache[thumb_url] = photo
            # Update UI from main thread via event
            self.master.event_generate("<<ThumbnailLoaded>>", when="tail", x=self.winfo_id(), y=list(self.thumbnail_cache.keys()).index(thumb_url))
        except Exception as e:
            print(f"Failed to load thumbnail {thumb_url}: {e}")

    def on_thumbnail_loaded(self, event):
        """Event handler to update treeview with loaded thumbnail."""
        thumb_url = list(self.thumbnail_cache.keys())[event.y]
        photo = self.thumbnail_cache[thumb_url]
        for item_id in self.tree.get_children():
            if self.tree.item(item_id, 'values')[1] == item_id: # Find item by URL
                self.tree.item(item_id, image=photo)
                break

    def on_history_select(self, event):
        """Handles selection in the history list."""
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection)
        url = item['values'][1]
        self.set_url_in_downloader(url)

    def filter_history(self, *args):
        """Filters the treeview based on the search entry."""
        query = self.search_var.get().lower()
        all_items = self.settings_manager.get_setting('history', [])
        
        # Detach all current items
        for item_id in self.tree.get_children():
            self.tree.detach(item_id)
            
        # Re-attach items that match the query
        for item_data in all_items:
            title = item_data['title'].lower()
            if query in title:
                # Check if item exists before trying to move it
                if self.tree.exists(item_data['url']):
                    self.tree.move(item_data['url'], '', 'end')


class SettingsFrame(ttk.Frame):
    """Frame for application settings."""
    def __init__(self, parent, settings_manager, app_style):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.style = app_style
        self.create_widgets()

    def create_widgets(self):
        """Create and grid the widgets for the settings."""
        settings_container = ttk.Frame(self, padding=20)
        settings_container.grid(row=0, column=0, sticky="nsew")

        # --- Theme Selector ---
        theme_label = ttk.Label(settings_container, text="Theme:")
        theme_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.theme_combo = ttk.Combobox(settings_container, values=self.style.theme_names(), state="readonly")
        self.theme_combo.set(self.settings_manager.get_setting('theme'))
        self.theme_combo.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        # --- Download Path ---
        path_label = ttk.Label(settings_container, text="Download Path:")
        path_label.grid(row=1, column=0, sticky="w", pady=(10, 5))

        self.path_var = tk.StringVar(value=self.settings_manager.get_setting('download_path'))
        path_display = ttk.Entry(settings_container, textvariable=self.path_var, state="readonly")
        path_display.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        change_path_btn = ttk.Button(settings_container, text="Change...", command=self.select_download_path)
        change_path_btn.grid(row=2, column=2, sticky="e", padx=(5, 0))

        settings_container.columnconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def change_theme(self, event):
        """Applies the selected theme and saves it."""
        theme = self.theme_combo.get()
        self.style.theme_use(theme)
        self.settings_manager.update_setting('theme', theme)

    def select_download_path(self):
        """Opens a dialog to select a new download directory."""
        path = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self.settings_manager.get_setting('download_path')
        )
        if path:
            self.settings_manager.update_setting('download_path', path)
            self.path_var.set(path)

class App(tb.Window):
    """Main application class."""
    def __init__(self):
        self.settings_manager = SettingsManager()
        theme = self.settings_manager.get_setting('theme', 'superhero')
        super().__init__(themename=theme)

        self.title("Pro Video Downloader")
        self.geometry("700x550")
        self.minsize(600, 400)

        self.create_widgets()
        
    def create_widgets(self):
        """Create the main widgets of the application."""
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(main_frame, bootstyle="primary")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Create frames
        self.downloader_frame = DownloaderFrame(self.notebook, self.settings_manager, self.update_status, self.update_history_tab)
        self.history_frame = HistoryFrame(self.notebook, self.settings_manager, self.set_url_in_downloader)
        self.settings_frame = SettingsFrame(self.notebook, self.settings_manager, self.style)

        # Add frames to notebook
        self.notebook.add(self.downloader_frame, text="Download")
        self.notebook.add(self.history_frame, text="History")
        self.notebook.add(self.settings_frame, text="Settings")

        # Status Bar
        self.status_var = tk.StringVar(value="Welcome!")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, anchor="w", bootstyle="inverse-primary", padding=5)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Bind event for thumbnail loading
        self.bind("<<ThumbnailLoaded>>", self.history_frame.on_thumbnail_loaded)

    def update_status(self, text, style="info"):
        """Updates the status bar text and style."""
        self.status_var.set(text)
        self.status_bar.config(bootstyle=f"inverse-{style}")

    def set_url_in_downloader(self, url):
        """Sets the URL in the downloader frame's entry and switches to it."""
        self.downloader_frame.url_entry.delete(0, tk.END)
        self.downloader_frame.url_entry.insert(0, url)
        self.notebook.select(self.downloader_frame)

    def update_history_tab(self):
        """Triggers a reload of the history tab."""
        self.history_frame.load_history()

if __name__ == "__main__":
    app = App()
    app.mainloop()