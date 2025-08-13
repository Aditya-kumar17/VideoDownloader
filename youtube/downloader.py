import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import json
import os
from PIL import Image, ImageTk
import io
import urllib.request
import functools

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("600x450")

        self.tabs = ttk.Notebook(root)
        self.youtube_tab = ttk.Frame(self.tabs)
        self.history_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.youtube_tab, text="YouTube")
        self.tabs.add(self.history_tab, text="History")
        self.tabs.pack(expand=1, fill="both")

    # YouTube Tab UI
        self.url_label = ttk.Label(self.youtube_tab, text="Enter Video URL:")
        self.url_label.pack(pady=10)
        self.url_entry = ttk.Entry(self.youtube_tab, width=60)
        self.url_entry.pack(pady=5)

        self.fetch_btn = ttk.Button(self.youtube_tab, text="Fetch Formats", command=self.fetch_formats)
        self.fetch_btn.pack(pady=10)

        self.format_list = tk.Listbox(self.youtube_tab, width=80, height=10)
        self.format_list.pack(pady=10)

        self.download_btn = ttk.Button(self.youtube_tab, text="Download Selected", command=self.download_selected)
        self.download_btn.pack(pady=10)

        self.progress = ttk.Progressbar(self.youtube_tab, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

    # History List in separate tab
        self.history_label = ttk.Label(self.history_tab, text="Download History:")
        self.history_label.pack(pady=5)
        self.history_canvas = tk.Canvas(self.history_tab, width=560, height=350)
        self.history_canvas.pack(pady=5)
        self.history_thumbnails = []  # Keep references to PhotoImage objects
        self.history_file = os.path.join(os.path.dirname(__file__), 'history.json')
        self.history = self.load_history()  # List of dicts: {url, title, thumbnail}
        self.refresh_history_list()
    def refresh_history_list(self):
        self.history_canvas.delete("all")
        self.history_thumbnails.clear()
        y = 10
        for idx, h in enumerate(self.history):
            thumb_img = None
            if h.get('thumbnail'):
                try:
                    with urllib.request.urlopen(h['thumbnail']) as u:
                        raw_data = u.read()
                    im = Image.open(io.BytesIO(raw_data)).resize((80, 45))
                    thumb_img = ImageTk.PhotoImage(im)
                    self.history_thumbnails.append(thumb_img)
                    self.history_canvas.create_image(10, y, anchor='nw', image=thumb_img)
                except Exception:
                    pass
            self.history_canvas.create_text(100, y+22, anchor='w', text=h['title'], font=("Arial", 12), tags=(f"entry{idx}",))
            self.history_canvas.tag_bind(f"entry{idx}", '<Button-1>', functools.partial(self._on_history_canvas_click, idx=idx))
            y += 55

    def _on_history_canvas_click(self, event, idx):
        self.on_history_canvas_click(idx)
    def on_history_canvas_click(self, idx):
        url = self.history[idx]['url']
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
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

        self.formats = []

    # Instagram Tab UI (placeholder)

    def fetch_formats(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return
        self.format_list.delete(0, tk.END)
        self.formats = []
        try:
            ydl_opts = {'listformats': True, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # Add to history if not already present
                title = info.get('title', url)
                thumbnail = info.get('thumbnail', '')
                if not any(h['url'] == url for h in self.history):
                    self.history.append({'url': url, 'title': title, 'thumbnail': thumbnail})
                    self.save_history()
                    self.refresh_history_list()
                important_exts = {'mp4', 'm4a'}
                for f in info.get('formats', []):
                    ext = f.get('ext', '')
                    if ext not in important_exts:
                        continue
                    # Hide storyboards and images
                    if f.get('vcodec', '') == 'images' or 'storyboard' in f.get('format_note', '').lower():
                        continue
                    height = f.get('height')
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
                    elif height >= 360:
                        res_str = '360p'
                    elif height >= 240:
                        res_str = '240p'
                    elif height >= 144:
                        res_str = '144p'
                    else:
                        res_str = f'{height}p'
                    fmt_str = (
                        f"Res: {res_str} | Type: {ext}"
                    )
                    self.format_list.insert(tk.END, fmt_str)
                    self.formats.append(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch formats: {e}")

    def on_history_select(self, event):
        selection = self.history_list.curselection()
        if not selection:
            return
        idx = selection[0]
        url = self.history[idx]['url']
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
    # That line is not a code

    def download_selected(self):
        selection = self.format_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a format to download.")
            return
        fmt = self.formats[selection[0]]
        url = self.url_entry.get().strip()
    # Check if selected format is available
        format_id = fmt.get('format_id')
        available_ids = [f.get('format_id') for f in self.formats]
        if format_id not in available_ids:
            messagebox.showerror("Error", "Selected format is not available for this video.")
            return
    # Check if selected format is video-only (no audio)
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        if vcodec != 'none' and (acodec == 'none' or acodec == 'null'):
            # Find best audio format
            audio_format = None
            for f in self.formats:
                if f.get('vcodec', 'none') == 'none' and f.get('acodec', 'none') != 'none':
                    audio_format = f['format_id']
                    break
            if audio_format:
                format_selector = f"{format_id}+{audio_format}"
            else:
                format_selector = f"{format_id}+bestaudio"
        else:
            format_selector = format_id
    # Get selected resolution for filename
        height = fmt.get('height')
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
        elif height >= 360:
            res_str = '360p'
        elif height >= 240:
            res_str = '240p'
        elif height >= 144:
            res_str = '144p'
        else:
            res_str = f'{height}p'
    # Use selected extension for output file
        ext = fmt.get('ext', 'mp4')
        ydl_opts = {
            'format': format_selector,
            'outtmpl': f'%(title)s_{res_str}.{ext}',
            'merge_output_format': ext if ext in ['mp4', 'm4a'] else 'mp4',
            'progress_hooks': [self.ytdlp_progress_hook],
        }
        self.progress['value'] = 0
        self.root.update_idletasks()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.progress['value'] = 100
            self.root.update_idletasks()
            messagebox.showinfo("Success", "Download completed!")
        except Exception as e:
            self.progress['value'] = 0
            self.root.update_idletasks()
            messagebox.showerror("Error", f"Download failed: {e}")
    def ytdlp_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = int(downloaded / total_bytes * 100)
                self.progress['value'] = percent
        elif d['status'] == 'finished':
            self.progress['value'] = 100

def main():
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
