import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("600x400")

        self.url_label = ttk.Label(root, text="Enter Video URL:")
        self.url_label.pack(pady=10)
        self.url_entry = ttk.Entry(root, width=60)
        self.url_entry.pack(pady=5)

        self.fetch_btn = ttk.Button(root, text="Fetch Formats", command=self.fetch_formats)
        self.fetch_btn.pack(pady=10)

        self.format_list = tk.Listbox(root, width=80, height=10)
        self.format_list.pack(pady=10)

        self.download_btn = ttk.Button(root, text="Download Selected", command=self.download_selected)
        self.download_btn.pack(pady=10)

        self.formats = []

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
                for f in info.get('formats', []):
                    height = f.get('height')
                    if height is None:
                        res_str = 'audio'
                    elif height >= 2160:
                        res_str = '4k'
                    elif height >= 1440:
                        res_str = '2k'
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
                        f"ID: {f.get('format_id', '')} | "
                        f"Type: {f.get('vcodec', 'none')}/{f.get('acodec', 'none')} | "
                        f"Res: {res_str} | "
                        f"Ext: {f.get('ext', '')} | "
                        f"Note: {f.get('format_note', '')}"
                    )
                    self.format_list.insert(tk.END, fmt_str)
                    self.formats.append(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch formats: {e}")

    def download_selected(self):
        selection = self.format_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a format to download.")
            return
        fmt = self.formats[selection[0]]
        url = self.url_entry.get().strip()
        ydl_opts = {
            'format': fmt['format_id'],
            'outtmpl': '%(title)s.%(ext)s',
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Success", "Download completed!")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {e}")

def main():
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
