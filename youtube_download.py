import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import scrapetube
import yt_dlp
import os
from datetime import datetime
import threading

class ShortsDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Shorts Downloader by Dat0o")
        self.root.geometry("950x780")
        
        self.shorts_list = []
        self.download_path = "./shorts_downloaded"
        self.setup_ui()
        self.configure_tree_style()
    
    def configure_tree_style(self):
        """Cấu hình style cho Treeview với border"""
        style = ttk.Style()
        
        style.configure("Bordered.Treeview",
                        borderwidth=1,
                        relief="solid",
                        rowheight=25,
                        fieldbackground="white")
        
        style.configure("Bordered.Treeview.Heading",
                        borderwidth=1,
                        relief="solid",
                        background="lightgray",
                        font=('Arial', 9, 'bold'))
        
        # Configure custom progressbar styles
        style.configure("Large.Horizontal.TProgressbar",
                        troughcolor='#e0e0e0',
                        background='#4CAF50',
                        lightcolor='#4CAF50',
                        darkcolor='#2E7D32',
                        borderwidth=1,
                        relief='solid')
        
        style.configure("Small.Horizontal.TProgressbar",
                        troughcolor='#e0e0e0',
                        background='#2196F3',
                        lightcolor='#2196F3',
                        darkcolor='#1976D2',
                        borderwidth=1,
                        relief='solid')
        
        style.map("Bordered.Treeview",
                  background=[('selected', '#0078d4')])
        
        style.map("Bordered.Treeview.Heading",
                  background=[('active', '#e1e1e1')])
    
    def setup_ui(self):
        # Frame chính
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # === URL INPUT SECTION ===
        url_frame = tk.LabelFrame(main_frame, text="📺 Kênh YouTube", font=('Arial', 10, 'bold'), padx=10, pady=8)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(url_frame, text="Link kênh:").pack(anchor=tk.W, pady=(0, 5))
        self.link_var = tk.StringVar()
        url_entry = tk.Entry(url_frame, textvariable=self.link_var, width=80, font=('Arial', 10))
        url_entry.pack(fill=tk.X)
        
        # === SETTINGS SECTION ===
        settings_frame = tk.LabelFrame(main_frame, text="⚙️ Cài đặt tải xuống", font=('Arial', 10, 'bold'), padx=10, pady=8)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Download path
        path_row = tk.Frame(settings_frame)
        path_row.pack(fill=tk.X, pady=2)
        
        tk.Label(path_row, text="📁 Thư mục lưu:", width=15, anchor='w').pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = tk.Entry(path_row, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        tk.Button(path_row, text="Chọn thư mục", command=self.choose_directory,
                  width=12).pack(side=tk.LEFT)
        
        # Row 2: Quality and Format settings
        quality_row = tk.Frame(settings_frame)
        quality_row.pack(fill=tk.X, pady=(8, 2))
        
        # Quality
        tk.Label(quality_row, text="🎥 Chất lượng:", width=15, anchor='w').pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="720p")
        quality_combo = ttk.Combobox(quality_row, textvariable=self.quality_var,
                                     values=["Tốt nhất", "1080p", "720p", "480p", "360p", "Nhỏ nhất"],
                                     state="readonly", width=12)
        quality_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # Format
        tk.Label(quality_row, text="📄 Format:", width=10, anchor='w').pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="mp4")
        format_combo = ttk.Combobox(quality_row, textvariable=self.format_var,
                                    values=["mp4", "webm", "mkv", "avi"],
                                    state="readonly", width=8)
        format_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # Audio
        tk.Label(quality_row, text="🔊 Audio:", width=10, anchor='w').pack(side=tk.LEFT)
        self.audio_var = tk.StringVar(value="Có")
        audio_combo = ttk.Combobox(quality_row, textvariable=self.audio_var,
                                   values=["Có", "Không", "Chỉ audio"],
                                   state="readonly", width=10)
        audio_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # === CONTROL SECTION ===
        control_frame = tk.LabelFrame(main_frame, text="🎮 Điều khiển", font=('Arial', 10, 'bold'), padx=10, pady=8)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 1: Main action buttons
        action_row = tk.Frame(control_frame)
        action_row.pack(fill=tk.X, pady=2)
        
        tk.Button(action_row, text="📋 Lấy danh sách Shorts",
                  command=self.get_shorts_list, width=20, height=1,
                  bg='#4CAF50', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(action_row, text="💾 Tải tất cả",
                  command=self.download_all, width=15, height=1,
                  bg='#2196F3', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        # Spacer
        tk.Frame(action_row).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status info (right aligned)
        self.videos_count_label = tk.Label(action_row, text="", font=('Arial', 9), fg='#666')
        self.videos_count_label.pack(side=tk.RIGHT)
        
        # Row 2: Range selection
        range_row = tk.Frame(control_frame)
        range_row.pack(fill=tk.X, pady=(8, 2))
        
        tk.Label(range_row, text="📊 Tải theo khoảng:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        tk.Label(range_row, text="Từ số:").pack(side=tk.LEFT, padx=(20, 5))
        self.start_var = tk.StringVar(value="1")
        start_entry = tk.Entry(range_row, textvariable=self.start_var, width=6, justify='center')
        start_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(range_row, text="đến số:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_var = tk.StringVar(value="10")
        end_entry = tk.Entry(range_row, textvariable=self.end_var, width=6, justify='center')
        end_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(range_row, text="▶️ Tải theo lựa chọn",
                  command=self.download_range, width=18,
                  bg='#FF9800', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        # === PROGRESS SECTION ===
        progress_frame = tk.LabelFrame(main_frame, text="📈 Tiến trình", font=('Arial', 10, 'bold'), padx=10, pady=8)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Overall progress
        tk.Label(progress_frame, text="Tổng thể:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        
        # Progress bar container với padding để tăng chiều cao
        overall_container = tk.Frame(progress_frame, height=25)
        overall_container.pack(fill=tk.X, pady=(2, 5))
        overall_container.pack_propagate(False)
        
        self.overall_progress = ttk.Progressbar(overall_container, mode='determinate',
                                                style="Large.Horizontal.TProgressbar")
        self.overall_progress.pack(fill=tk.BOTH, expand=True, pady=3)
        
        self.overall_status = tk.Label(progress_frame, text="Sẵn sàng", anchor=tk.W, font=('Arial', 9))
        self.overall_status.pack(anchor=tk.W)
        
        # Current video progress
        tk.Label(progress_frame, text="Video hiện tại:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(8, 0))
        
        # Progress bar container cho current
        current_container = tk.Frame(progress_frame, height=20)
        current_container.pack(fill=tk.X, pady=(2, 5))
        current_container.pack_propagate(False)
        
        self.current_progress = ttk.Progressbar(current_container, mode='determinate',
                                                style="Small.Horizontal.TProgressbar")
        self.current_progress.pack(fill=tk.BOTH, expand=True, pady=2)
        
        self.current_status = tk.Label(progress_frame, text="", anchor=tk.W, font=('Arial', 8))
        self.current_status.pack(anchor=tk.W)
        
        # === VIDEO LIST SECTION ===
        list_frame = tk.LabelFrame(main_frame, text="📋 Danh sách Shorts", font=('Arial', 10, 'bold'), padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview frame với border
        tree_frame = tk.Frame(list_frame, relief=tk.SUNKEN, borderwidth=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for shorts list
        columns = ('STT', 'Tiêu đề', 'Thời lượng', 'Ngày tải lên', 'Trạng thái')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                 height=10, style="Bordered.Treeview")
        
        # Define headings
        self.tree.heading('STT', text='STT', anchor='center')
        self.tree.heading('Tiêu đề', text='Tiêu đề', anchor='w')
        self.tree.heading('Thời lượng', text='Thời lượng (s)', anchor='center')
        self.tree.heading('Ngày tải lên', text='Ngày tải lên', anchor='center')
        self.tree.heading('Trạng thái', text='Trạng thái', anchor='center')
        
        # Configure columns
        self.tree.column('STT', width=50, anchor='center', minwidth=50)
        self.tree.column('Tiêu đề', width=350, anchor='w', minwidth=200)
        self.tree.column('Thời lượng', width=100, anchor='center', minwidth=80)
        self.tree.column('Ngày tải lên', width=100, anchor='center', minwidth=90)
        self.tree.column('Trạng thái', width=120, anchor='center', minwidth=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Tags cho styling
        self.tree.tag_configure('oddrow', background='#f8f9fa')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.tag_configure('pending', foreground='#6c757d')
        self.tree.tag_configure('downloading', foreground='#0066cc', background='#e3f2fd')
        self.tree.tag_configure('completed', foreground='#28a745', background='#d4edda')
        self.tree.tag_configure('error', foreground='#dc3545', background='#f8d7da')
        
        # === LOG SECTION ===
        log_frame = tk.LabelFrame(main_frame, text="📝 Nhật ký hoạt động", font=('Arial', 10, 'bold'), padx=5, pady=5)
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80,
                                                  font=('Consolas', 9), bg='#f8f9fa')
        self.log_text.pack(fill=tk.BOTH, padx=5, pady=5)
    
    def get_download_format(self):
        """Tạo format string cho yt-dlp dựa vào settings"""
        quality = self.quality_var.get()
        format_ext = self.format_var.get()
        audio_choice = self.audio_var.get()
        
        if quality == "Tốt nhất":
            video_format = "best"
        elif quality == "Nhỏ nhất":
            video_format = "worst"
        else:
            height = quality.replace('p', '')
            video_format = f"best[height<={height}]"
        
        if audio_choice == "Chỉ audio":
            return "bestaudio/best"
        elif audio_choice == "Không":
            return f"{video_format}[acodec=none]/{video_format}"
        else:
            return f"{video_format}[ext={format_ext}]/best[ext={format_ext}]/{video_format}/best"
    
    def choose_directory(self):
        """Chọn thư mục lưu file"""
        directory = filedialog.askdirectory(initialdir=self.download_path)
        if directory:
            self.download_path = directory
            self.path_var.set(directory)
            self.log(f"📁 Đã chọn thư mục: {directory}")
    
    def log(self, message):
        """Thêm message vào log area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_tree_status(self, index, status):
        """Cập nhật trạng thái trong tree với màu sắc"""
        items = self.tree.get_children()
        if 0 <= index < len(items):
            item = items[index]
            values = list(self.tree.item(item)['values'])
            values[4] = status
            
            if status == "Chưa tải":
                tag = 'pending'
            elif status == "Đang tải...":
                tag = 'downloading'
            elif status == "Hoàn thành":
                tag = 'completed'
            elif status == "Lỗi":
                tag = 'error'
            else:
                tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            
            self.tree.item(item, values=values, tags=(tag,))
            self.root.update()
    
    def get_shorts_list(self):
        """Lấy danh sách shorts từ kênh"""
        url = self.link_var.get().strip()
        if not url.startswith("https://www.youtube.com/@"):
            messagebox.showwarning("❌ Lỗi", "Vui lòng nhập link kênh dạng https://www.youtube.com/@username")
            return
        
        self.log("🔍 Bắt đầu quét kênh để lấy danh sách Shorts...")
        self.overall_status.config(text="🔍 Đang quét kênh...")
        self.videos_count_label.config(text="")
        
        def fetch_shorts():
            try:
                # Clear existing data
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.shorts_list = []
                
                videos = scrapetube.get_channel(channel_url=url, limit=500)
                shorts_data = []
                
                for video in videos:
                    video_id = video['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    try:
                        ydl_opts = {'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(video_url, download=False)
                            duration = info.get('duration', 0)
                            
                            if duration <= 180:
                                upload_date = info.get('upload_date', '20000101')
                                formatted_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%d/%m/%Y')
                                
                                shorts_data.append({
                                    'video_id': video_id,
                                    'title': info.get('title', 'Unknown'),
                                    'duration': duration,
                                    'upload_date': upload_date,
                                    'formatted_date': formatted_date,
                                    'url': video_url
                                })
                                
                                self.log(f"✅ Tìm thấy: {info.get('title', 'Unknown')} ({duration}s)")
                    
                    except Exception as e:
                        self.log(f"⚠️ Lỗi khi xử lý video {video_id}: {e}")
                        continue
                
                shorts_data.sort(key=lambda x: x['upload_date'], reverse=True)
                self.shorts_list = shorts_data
                
                for i, short in enumerate(shorts_data, 1):
                    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                    self.tree.insert('', 'end', values=(
                        i,
                        short['title'][:50] + "..." if len(short['title']) > 50 else short['title'],
                        short['duration'],
                        short['formatted_date'],
                        "Chưa tải"
                    ), tags=(tag,))
                
                count = len(shorts_data)
                self.log(f"🎉 Hoàn thành! Tìm thấy {count} video Shorts")
                self.overall_status.config(text=f"✅ Tìm thấy {count} video Shorts")
                self.videos_count_label.config(text=f"📊 Tổng: {count} videos")
                
                if shorts_data:
                    self.end_var.set(str(len(shorts_data)))
            
            except Exception as e:
                self.log(f"❌ Lỗi khi lấy danh sách: {e}")
                messagebox.showerror("❌ Lỗi", f"Lỗi khi lấy danh sách video: {e}")
                self.overall_status.config(text="❌ Lỗi khi quét kênh")
        
        threading.Thread(target=fetch_shorts, daemon=True).start()
    
    def progress_hook(self, d):
        """Hook function để theo dõi tiến trình download"""
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    percent = 0
                
                self.current_progress['value'] = percent
                
                speed = d.get('speed', 0)
                if speed:
                    speed_str = f"{speed/1024/1024:.1f} MB/s" if speed > 1024*1024 else f"{speed/1024:.1f} KB/s"
                else:
                    speed_str = "0 KB/s"
                
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                if total:
                    size_str = f"{downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB"
                else:
                    size_str = f"{downloaded/1024/1024:.1f} MB"
                
                self.current_status.config(text=f"📥 {percent:.1f}% - {speed_str} - {size_str}")
                self.root.update()
            
            except Exception as e:
                pass
        
        elif d['status'] == 'finished':
            self.current_progress['value'] = 100
            self.current_status.config(text="✅ Hoàn thành tải video")
            self.root.update()
    
    def download_short(self, short_info, index, total_index):
        """Tải một video short"""
        download_path = self.path_var.get().strip() or self.download_path
        download_format = self.get_download_format()
        audio_choice = self.audio_var.get()
        
        if audio_choice == "Chỉ audio":
            output_template = f'{download_path}/%(upload_date)s_%(title)s.%(ext)s'
        else:
            format_ext = self.format_var.get()
            output_template = f'{download_path}/%(upload_date)s_%(title)s.{format_ext}'
        
        ydl_opts = {
            'format': download_format,
            'outtmpl': output_template,
            'quiet': True,
            'progress_hooks': [self.progress_hook],
        }
        
        try:
            self.update_tree_status(index, "Đang tải...")
            self.current_status.config(text=f"📥 Đang tải: {short_info['title'][:40]}...")
            self.current_progress['value'] = 0
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                quality = self.quality_var.get()
                self.log(f"📥 [{total_index}] Đang tải ({quality}): {short_info['title']}")
                ydl.download([short_info['url']])
                
                self.update_tree_status(index, "Hoàn thành")
                self.log(f"✅ [{total_index}] Hoàn thành: {short_info['title']}")
                return True
        
        except Exception as e:
            self.update_tree_status(index, "Lỗi")
            self.log(f"❌ [{total_index}] Lỗi: {e}")
            return False
    
    def download_range(self):
        """Tải video theo range đã chọn"""
        if not self.shorts_list:
            messagebox.showwarning("❌ Lỗi", "Vui lòng lấy danh sách Shorts trước!")
            return
        
        try:
            start_idx = int(self.start_var.get()) - 1
            end_idx = int(self.end_var.get())
            
            if start_idx < 0 or end_idx > len(self.shorts_list) or start_idx >= end_idx:
                messagebox.showwarning("❌ Lỗi", "Số thứ tự không hợp lệ!")
                return
        
        except ValueError:
            messagebox.showwarning("❌ Lỗi", "Vui lòng nhập số hợp lệ!")
            return
        
        def download_task():
            download_path = self.path_var.get().strip() or self.download_path
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            
            count = 0
            total = end_idx - start_idx
            
            self.overall_progress['maximum'] = total
            self.overall_progress['value'] = 0
            
            quality = self.quality_var.get()
            format_ext = self.format_var.get()
            audio_choice = self.audio_var.get()
            
            self.log(f"🚀 Bắt đầu tải từ video {start_idx + 1} đến {end_idx}")
            self.log(f"⚙️ Settings: {quality}, {format_ext}, Audio: {audio_choice}")
            self.overall_status.config(text=f"📥 Đang tải 0/{total} video...")
            
            for i in range(start_idx, end_idx):
                if self.download_short(self.shorts_list[i], i, i + 1):
                    count += 1
                
                progress = i - start_idx + 1
                self.overall_progress['value'] = progress
                self.overall_status.config(text=f"📥 Đang tải {progress}/{total} video...")
            
            self.overall_status.config(text=f"🎉 Hoàn thành! {count}/{total} video")
            self.current_status.config(text="")
            self.current_progress['value'] = 0
            
            self.log(f"🎉 Hoàn thành! Đã tải {count}/{total} video về {download_path}")
            messagebox.showinfo("🎉 Hoàn thành", f"Đã tải {count}/{total} video Shorts thành công!")
        
        threading.Thread(target=download_task, daemon=True).start()
    
    def download_all(self):
        """Tải tất cả shorts"""
        if not self.shorts_list:
            messagebox.showwarning("❌ Lỗi", "Vui lòng lấy danh sách Shorts trước!")
            return
        
        self.start_var.set("1")
        self.end_var.set(str(len(self.shorts_list)))
        self.download_range()

if __name__ == "__main__":
    root = tk.Tk()
    app = ShortsDownloader(root)
    root.mainloop()
