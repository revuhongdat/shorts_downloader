import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import yt_dlp
import os
from datetime import datetime, timedelta
import threading

class ShortsDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Shorts YouTube Downloader - by Dat0o")
        self.root.geometry("1100x820")
        
        self.shorts_list = []
        self.download_path = "./shorts_downloaded"
        self.cookies_path = ""  # tùy chọn
        
        self.setup_ui()
        self.configure_tree_style()
    
    # ------------- UI helpers (thread-safe) -------------
    def safe_ui(self, func, *args, **kwargs):
        self.root.after(0, lambda: func(*args, **kwargs))
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def configure_tree_style(self):
        style = ttk.Style()
        style.configure("Bordered.Treeview",
                        borderwidth=1, relief="solid",
                        rowheight=25, fieldbackground="white")
        style.configure("Bordered.Treeview.Heading",
                        borderwidth=1, relief="solid",
                        background="lightgray", font=('Arial', 9, 'bold'))
        style.configure("Large.Horizontal.TProgressbar",
                        troughcolor='#e0e0e0', background='#4CAF50',
                        lightcolor='#4CAF50', darkcolor='#2E7D32',
                        borderwidth=1, relief='solid')
        style.configure("Small.Horizontal.TProgressbar",
                        troughcolor='#e0e0e0', background='#2196F3',
                        lightcolor='#2196F3', darkcolor='#1976D2',
                        borderwidth=1, relief='solid')
        style.map("Bordered.Treeview", background=[('selected', '#0078d4')])
        style.map("Bordered.Treeview.Heading", background=[('active', '#e1e1e1')])
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        
        # URL
        url_frame = tk.LabelFrame(main_frame, text="📺 Kênh YouTube", font=('Arial', 10, 'bold'), padx=10, pady=8)
        url_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(url_frame, text="Link kênh (ví dụ: https://www.youtube.com/@abc):").pack(anchor=tk.W, pady=(0, 5))
        self.link_var = tk.StringVar()
        url_entry = tk.Entry(url_frame, textvariable=self.link_var, width=80, font=('Arial', 10))
        url_entry.pack(fill=tk.X)
        
        # Combined filters + settings
        combined_frame = tk.Frame(main_frame)
        combined_frame.pack(fill=tk.X, pady=(10, 10))
        
        # --- Time filter
        filter_frame = tk.LabelFrame(combined_frame, text="📅 Khoảng thời gian", font=('Arial', 10, 'bold'), padx=10, pady=8)
        filter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        time_options_frame = tk.Frame(filter_frame); time_options_frame.pack(fill=tk.X, pady=2)
        self.time_filter_var = tk.StringVar(value="30d")
        time_options = [("Tất cả", "all"), ("24h", "1d"), ("7d", "7d"), ("30d", "30d"),
                        ("90d", "90d"), ("1y", "1y"), ("Tùy chọn", "custom")]
        for text, value in time_options:
            tk.Radiobutton(time_options_frame, text=text, variable=self.time_filter_var, value=value) \
                .pack(side=tk.LEFT, padx=3)
        
        custom_row = tk.Frame(filter_frame); custom_row.pack(fill=tk.X, pady=(8, 2))
        tk.Label(custom_row, text="Từ ngày:", width=8, anchor='w').pack(side=tk.LEFT)
        self.from_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y"))
        tk.Entry(custom_row, textvariable=self.from_date_var, width=12, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 8))
        tk.Label(custom_row, text="Đến ngày:", width=8, anchor='w').pack(side=tk.LEFT)
        self.to_date_var = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        tk.Entry(custom_row, textvariable=self.to_date_var, width=12, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 8))
        tk.Label(custom_row, text="(dd/mm/yyyy)", font=('Arial', 7), fg='gray').pack(side=tk.LEFT, padx=(5,0))
        
        # --- Settings
        settings_frame = tk.LabelFrame(combined_frame, text="⚙️ Cài đặt tải xuống", font=('Arial', 10, 'bold'), padx=10, pady=8)
        settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        path_row = tk.Frame(settings_frame); path_row.pack(fill=tk.X, pady=2)
        tk.Label(path_row, text="📁 Thư mục:", width=12, anchor='w').pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.download_path)
        tk.Entry(path_row, textvariable=self.path_var, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 5), fill=tk.X, expand=True)
        tk.Button(path_row, text="...", command=self.choose_directory, width=3, font=('Arial', 8)).pack(side=tk.LEFT)
        
        quality_row = tk.Frame(settings_frame); quality_row.pack(fill=tk.X, pady=(8, 2))
        tk.Label(quality_row, text="🎥 Chất lượng:", width=12, anchor='w').pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="720p")
        ttk.Combobox(quality_row, textvariable=self.quality_var,
                     values=["Tốt nhất","1080p","720p","480p","360p","Nhỏ nhất"],
                     state="readonly", width=10, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 10))
        
        tk.Label(quality_row, text="📄 Format:", width=8, anchor='w').pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="mp4")
        ttk.Combobox(quality_row, textvariable=self.format_var,
                     values=["mp4","webm","mkv","avi"],
                     state="readonly", width=8, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 10))
        
        tk.Label(quality_row, text="🔊 Audio:", width=8, anchor='w').pack(side=tk.LEFT)
        self.audio_var = tk.StringVar(value="Có")
        ttk.Combobox(quality_row, textvariable=self.audio_var,
                     values=["Có","Không","Chỉ audio"],
                     state="readonly", width=10, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2, 10))
        
        # Optional cookies
        cookie_row = tk.Frame(settings_frame); cookie_row.pack(fill=tk.X, pady=(8,2))
        tk.Label(cookie_row, text="🍪 Cookies:", width=12, anchor='w').pack(side=tk.LEFT)
        self.cookies_var = tk.StringVar(value="")
        tk.Entry(cookie_row, textvariable=self.cookies_var, font=('Arial', 9)).pack(side=tk.LEFT, padx=(2,5), fill=tk.X, expand=True)
        tk.Button(cookie_row, text="Chọn", command=self.choose_cookies, width=6).pack(side=tk.LEFT)
        tk.Label(settings_frame, text="(Tuỳ chọn, dùng khi kênh rất lớn hoặc bị chặn)", fg="#666", font=('Arial', 8)).pack(anchor='w')
        
        # Controls
        control_frame = tk.LabelFrame(main_frame, text="🎮 Điều khiển", font=('Arial', 10, 'bold'), padx=10, pady=8)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        action_row = tk.Frame(control_frame); action_row.pack(fill=tk.X, pady=2)
        tk.Button(action_row, text="📋 Lấy danh sách Shorts",
                  command=self.get_shorts_list, width=20, height=1,
                  bg='#4CAF50', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(action_row, text="💾 Tải tất cả",
                  command=self.download_all, width=15, height=1,
                  bg='#2196F3', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        tk.Frame(action_row).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.videos_count_label = tk.Label(action_row, text="", font=('Arial', 9), fg='#666')
        self.videos_count_label.pack(side=tk.RIGHT)
        
        range_row = tk.Frame(control_frame); range_row.pack(fill=tk.X, pady=(8, 2))
        tk.Label(range_row, text="📊 Tải theo khoảng:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        tk.Label(range_row, text="Từ số:").pack(side=tk.LEFT, padx=(20, 5))
        self.start_var = tk.StringVar(value="1")
        tk.Entry(range_row, textvariable=self.start_var, width=6, justify='center').pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(range_row, text="đến số:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_var = tk.StringVar(value="10")
        tk.Entry(range_row, textvariable=self.end_var, width=6, justify='center').pack(side=tk.LEFT, padx=(0, 15))
        tk.Button(range_row, text="▶️ Tải theo lựa chọn",
                  command=self.download_range, width=18,
                  bg='#FF9800', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        # Progress
        progress_frame = tk.LabelFrame(main_frame, text="📈 Tiến trình", font=('Arial', 10, 'bold'), padx=10, pady=8)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(progress_frame, text="Tổng thể:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        overall_container = tk.Frame(progress_frame, height=25)
        overall_container.pack(fill=tk.X, pady=(2, 5))
        overall_container.pack_propagate(False)
        self.overall_progress = ttk.Progressbar(overall_container, mode='determinate',
                                                style="Large.Horizontal.TProgressbar")
        self.overall_progress.pack(fill=tk.BOTH, expand=True, pady=3)
        self.overall_status = tk.Label(progress_frame, text="Sẵn sàng", anchor=tk.W, font=('Arial', 9))
        self.overall_status.pack(anchor=tk.W)
        
        tk.Label(progress_frame, text="Video hiện tại:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(8, 0))
        current_container = tk.Frame(progress_frame, height=20)
        current_container.pack(fill=tk.X, pady=(2, 5))
        current_container.pack_propagate(False)
        self.current_progress = ttk.Progressbar(current_container, mode='determinate',
                                                style="Small.Horizontal.TProgressbar")
        self.current_progress.pack(fill=tk.BOTH, expand=True, pady=2)
        self.current_status = tk.Label(progress_frame, text="", anchor=tk.W, font=('Arial', 8))
        self.current_status.pack(anchor=tk.W)
        
        # List
        list_frame = tk.LabelFrame(main_frame, text="📋 Danh sách Shorts (≤180s)", font=('Arial', 10, 'bold'), padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tree_frame = tk.Frame(list_frame, relief=tk.SUNKEN, borderwidth=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('STT', 'Tiêu đề', 'Thời lượng', 'Ngày tải lên', 'Trạng thái')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8, style="Bordered.Treeview")
        self.tree.heading('STT', text='STT', anchor='center')
        self.tree.heading('Tiêu đề', text='Tiêu đề', anchor='w')
        self.tree.heading('Thời lượng', text='Thời lượng (s)', anchor='center')
        self.tree.heading('Ngày tải lên', text='Ngày tải lên', anchor='center')
        self.tree.heading('Trạng thái', text='Trạng thái', anchor='center')
        self.tree.column('STT', width=50, anchor='center', minwidth=50)
        self.tree.column('Tiêu đề', width=450, anchor='w', minwidth=250)
        self.tree.column('Thời lượng', width=100, anchor='center', minwidth=80)
        self.tree.column('Ngày tải lên', width=120, anchor='center', minwidth=100)
        self.tree.column('Trạng thái', width=120, anchor='center', minwidth=100)
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1); tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.tag_configure('oddrow', background='#f8f9fa')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.tag_configure('pending', foreground='#6c757d')
        self.tree.tag_configure('downloading', foreground='#0066cc', background='#e3f2fd')
        self.tree.tag_configure('completed', foreground='#28a745', background='#d4edda')
        self.tree.tag_configure('error', foreground='#dc3545', background='#f8d7da')
        
        # Log
        log_frame = tk.LabelFrame(main_frame, text="📝 Nhật ký hoạt động", font=('Arial', 10, 'bold'), padx=5, pady=5)
        log_frame.pack(fill=tk.X)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80, font=('Consolas', 9), bg='#f8f9fa')
        self.log_text.pack(fill=tk.BOTH, padx=5, pady=5)
    
    # ------------- Utils -------------
    def choose_directory(self):
        directory = filedialog.askdirectory(initialdir=self.download_path)
        if directory:
            self.download_path = directory
            self.path_var.set(directory)
            self.safe_ui(self.log, f"📁 Đã chọn thư mục: {directory}")
    
    def choose_cookies(self):
        path = filedialog.askopenfilename(title="Chọn cookies.txt",
                                          filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if path:
            self.cookies_path = path
            self.cookies_var.set(path)
            self.safe_ui(self.log, f"🍪 Dùng cookies: {path}")
    
    def parse_date_string(self, date_str):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return None
    
    def get_time_range(self):
        filter_type = self.time_filter_var.get()
        now = datetime.now()
        if filter_type == "all":
            return None, None, "tất cả thời gian"
        elif filter_type == "custom":
            from_date = self.parse_date_string(self.from_date_var.get())
            to_date = self.parse_date_string(self.to_date_var.get())
            if not from_date or not to_date:
                messagebox.showwarning("❌ Lỗi", "Định dạng ngày không hợp lệ! Sử dụng dd/mm/yyyy")
                return None, None, None
            if from_date > to_date:
                messagebox.showwarning("❌ Lỗi", "Ngày bắt đầu phải nhỏ hơn ngày kết thúc!")
                return None, None, None
            to_date = to_date.replace(hour=23, minute=59, second=59)
            return from_date, to_date, f"từ {from_date.strftime('%d/%m/%Y')} đến {to_date.strftime('%d/%m/%Y')}"
        else:
            mapping = {
                "1d": (now - timedelta(days=1), "24 giờ qua"),
                "7d": (now - timedelta(days=7), "7 ngày qua"),
                "30d": (now - timedelta(days=30), "30 ngày qua"),
                "90d": (now - timedelta(days=90), "90 ngày qua"),
                "1y": (now - timedelta(days=365), "1 năm qua"),
            }
            cutoff, name = mapping[filter_type]
            return cutoff, now, name
    
    def is_video_in_time_range(self, up_dt, from_date, to_date):
        if from_date is None and to_date is None:
            return True
        if up_dt is None:
            # Không biết ngày → ĐỪNG loại
            return True
        if from_date and to_date:
            return from_date <= up_dt <= to_date
        if from_date:
            return up_dt >= from_date
        return True
    
    def get_shorts_url(self, video_id):
        return f"https://www.youtube.com/shorts/{video_id}"
    
    # ------------- Fetch Shorts list -------------
    def get_channel_videos_with_ytdlp(self, channel_url, limit=2000):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,          # lấy danh sách nhanh, sâu
            'playlistend': limit,
            'ignoreerrors': True,
            'retries': 5,
            'extractor_args': {
                'youtube': {
                    'tab': ['shorts'],     # ÉP tab Shorts
                }
            }
        }
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.safe_ui(self.log, "🔄 Đang lấy tab Shorts của kênh...")
                url = channel_url.rstrip('/')
                if not url.endswith('/shorts'):
                    url = url + '/shorts'
                info = ydl.extract_info(url, download=False)
                if not info:
                    return []
                return info.get('entries', [])
        except Exception as e:
            self.safe_ui(self.log, f"❌ Lỗi yt-dlp khi lấy danh sách: {e}")
            return []
    
    def update_tree_status(self, index, status):
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
    
    def get_shorts_list(self):
        url = self.link_var.get().strip()
        if not (url.startswith("https://www.youtube.com/@") or "youtube.com/channel/" in url):
            messagebox.showwarning("❌ Lỗi", "Vui lòng nhập link kênh dạng https://www.youtube.com/@username hoặc /channel/ID")
            return
        
        from_date, to_date, range_name = self.get_time_range()
        if range_name is None:
            return
        
        self.safe_ui(self.log, f"🔍 Lấy video ≤180s {range_name}...")
        self.safe_ui(self.overall_status.config, text="🔍 Đang quét kênh...")
        self.safe_ui(self.videos_count_label.config, text="")
        
        def fetch_shorts():
            try:
                self.safe_ui(lambda: [self.tree.delete(i) for i in self.tree.get_children()])
                self.shorts_list = []
                
                videos = self.get_channel_videos_with_ytdlp(url, limit=2000)
                if not videos:
                    self.safe_ui(self.log, "❌ Không thể lấy danh sách video từ kênh!")
                    messagebox.showerror("❌ Lỗi", "Không thể lấy danh sách video từ kênh!")
                    return
                
                shorts_data = []
                checked_count = 0
                skipped_by_time = 0
                skipped_by_duration = 0
                
                self.safe_ui(self.log, f"📊 Đã lấy {len(videos)} mục, bắt đầu phân tích...")
                
                for video_info in videos:
                    if not video_info:
                        continue
                    checked_count += 1
                    if checked_count % 50 == 0:
                        self.safe_ui(self.log, f"📊 Phân tích {checked_count}/{len(videos)}... Tìm thấy {len(shorts_data)} Shorts")
                    
                    try:
                        # id/title
                        vid = video_info.get('id') or video_info.get('url') or ""
                        if not vid:
                            continue
                        # Một số mục có 'url' dạng '/watch?v=XXXX' → cắt id
                        if isinstance(vid, str) and 'watch?v=' in vid:
                            vid = vid.split('watch?v=')[-1].split('&')[0]
                        
                        # duration
                        duration = video_info.get('duration')
                        # Nếu không có duration: vẫn nhận (Shorts thường <=60/90s)
                        if duration is not None and duration > 180:
                            skipped_by_duration += 1
                            continue
                        
                        # thời gian
                        upload_date_raw = video_info.get('upload_date')
                        timestamp = video_info.get('timestamp') or video_info.get('release_timestamp')
                        if timestamp:
                            up_dt = datetime.fromtimestamp(timestamp)
                            up_date_str = up_dt.strftime('%Y%m%d')
                        elif upload_date_raw:
                            try:
                                up_dt = datetime.strptime(upload_date_raw, '%Y%m%d')
                                up_date_str = upload_date_raw
                            except Exception:
                                up_dt = None
                                up_date_str = None
                        else:
                            up_dt = None
                            up_date_str = None
                        
                        if not self.is_video_in_time_range(up_dt, from_date, to_date):
                            skipped_by_time += 1
                            continue
                        
                        formatted_date = up_dt.strftime('%d/%m/%Y') if up_dt else '—'
                        
                        shorts_data.append({
                            'video_id': vid,
                            'title': video_info.get('title', 'Unknown'),
                            'duration': int(duration) if duration is not None else 0,
                            'upload_date': up_date_str or '00000000',
                            'formatted_date': formatted_date,
                            'url': self.get_shorts_url(vid),
                            'watch_url': f"https://www.youtube.com/watch?v={vid}",
                        })
                    
                    except Exception as e:
                        self.safe_ui(self.log, f"⚠️ Lỗi khi phân tích video: {e}")
                        continue
                
                # sort: item có ngày lên trước, sau đó theo ngày giảm dần
                shorts_data.sort(key=lambda x: (x['upload_date'] == '00000000', x['upload_date']), reverse=True)
                self.shorts_list = shorts_data
                
                def fill_tree():
                    for i, short in enumerate(shorts_data, 1):
                        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                        title = short['title'] or 'Unknown'
                        title = (title[:55] + '...') if len(title) > 55 else title
                        self.tree.insert('', 'end', values=(
                            i, title, short['duration'], short['formatted_date'], "Chưa tải"
                        ), tags=(tag,))
                self.safe_ui(fill_tree)
                
                count = len(shorts_data)
                self.safe_ui(self.log, f"🎉 Hoàn thành! Tìm thấy {count} Shorts (≤180s) {range_name}")
                self.safe_ui(self.log, f"📊 Phân tích: {checked_count} mục | Bỏ qua: {skipped_by_time} (thời gian) + {skipped_by_duration} (>180s)")
                self.safe_ui(self.overall_status.config, text=f"✅ Tìm thấy {count} Shorts")
                self.safe_ui(self.videos_count_label.config, text=f"📊 Tổng: {count} videos")
                if count:
                    self.safe_ui(self.end_var.set, str(count))
            
            except Exception as e:
                self.safe_ui(self.log, f"❌ Lỗi khi lấy danh sách: {e}")
                messagebox.showerror("❌ Lỗi", f"Lỗi khi lấy danh sách video: {e}")
                self.safe_ui(self.overall_status.config, text="❌ Lỗi khi quét kênh")
        
        threading.Thread(target=fetch_shorts, daemon=True).start()
    
    # ------------- Download -------------
    def get_download_format(self):
        quality = self.quality_var.get()
        if quality == "Tốt nhất":
            return "bv*+ba/b"
        elif quality == "Nhỏ nhất":
            return "worst"
        else:
            h = ''.join(ch for ch in quality if ch.isdigit())
            return f"bv*[height<={h}]+ba/b[height<={h}]"
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                if 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    percent = 0.0
                
                speed = d.get('speed') or 0
                speed_str = f"{speed/1024/1024:.1f} MB/s" if speed > 1024*1024 else f"{speed/1024:.1f} KB/s"
                
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total:
                    size_str = f"{downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB"
                else:
                    size_str = f"{downloaded/1024/1024:.1f} MB"
                
                self.safe_ui(self.current_progress.configure, value=percent)
                self.safe_ui(self.current_status.config, text=f"📥 {percent:.1f}% - {speed_str} - {size_str}")
            except Exception:
                pass
        
        elif d['status'] == 'finished':
            self.safe_ui(self.current_progress.configure, value=100)
            self.safe_ui(self.current_status.config, text="✅ Hoàn thành tải video")
    
    def download_short(self, short_info, index, total_index):
        download_path = self.path_var.get().strip() or self.download_path
        fmt = self.get_download_format()
        audio_choice = self.audio_var.get()
        container = self.format_var.get()
        
        outtmpl = f'{download_path}/%(upload_date,unknown)s_%(title).150B.%(ext)s'
        ydl_opts = {
            'format': ("bestaudio/best" if audio_choice == "Chỉ audio" else fmt),
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
            'noprogress': True,
            'retries': 5,
            'fragment_retries': 5,
            'concurrent_fragment_downloads': 4,
            'ignoreerrors': False,
        }
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
        
        # Merge/convert (nếu không phải "Chỉ audio")
        if audio_choice != "Chỉ audio":
            # Gợi ý container mong muốn (không cưỡng ép nếu không hỗ trợ)
            ydl_opts['merge_output_format'] = container
            # Nếu cần chuyển container:
            if container in ('mp4', 'mkv', 'webm', 'avi'):
                ydl_opts.setdefault('postprocessors', [])
                # Video convertor (chỉ chuyển container nếu cần)
                ydl_opts['postprocessors'].append({'key': 'FFmpegVideoConvertor', 'preferedformat': container})
        
        try:
            self.safe_ui(self.update_tree_status, index, "Đang tải...")
            short_title = (short_info['title'][:40] + '...') if len(short_info['title']) > 40 else short_info['title']
            self.safe_ui(self.current_status.config, text=f"📥 Đang tải: {short_title}")
            self.safe_ui(self.current_progress.configure, value=0)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                quality = self.quality_var.get()
                self.safe_ui(self.log, f"📥 [{total_index}] yt-dlp tải ({quality}): {short_info['title']}")
                try:
                    ydl.download([short_info['url']])
                except Exception:
                    self.safe_ui(self.log, f"⚠️ [{total_index}] Lỗi URL Shorts, thử URL watch...")
                    ydl.download([short_info['watch_url']])
                
                self.safe_ui(self.update_tree_status, index, "Hoàn thành")
                self.safe_ui(self.log, f"✅ [{total_index}] Hoàn thành: {short_info['title']}")
                return True
        
        except Exception as e:
            self.safe_ui(self.update_tree_status, index, "Lỗi")
            self.safe_ui(self.log, f"❌ [{total_index}] Lỗi: {e}")
            return False
    
    def download_range(self):
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
            os.makedirs(download_path, exist_ok=True)
            
            total = end_idx - start_idx
            done = 0
            self.safe_ui(self.overall_progress.configure, maximum=total, value=0)
            
            quality = self.quality_var.get()
            container = self.format_var.get()
            audio_choice = self.audio_var.get()
            self.safe_ui(self.log, f"🚀 Bắt đầu tải từ video {start_idx + 1} đến {end_idx}")
            self.safe_ui(self.log, f"⚙️ Settings: {quality}, {container}, Audio: {audio_choice}, Cookies: {'Có' if self.cookies_path else 'Không'}")
            self.safe_ui(self.overall_status.config, text=f"📥 Đang tải 0/{total} video...")
            
            for i in range(start_idx, end_idx):
                if self.download_short(self.shorts_list[i], i, i + 1):
                    done += 1
                progress = i - start_idx + 1
                self.safe_ui(self.overall_progress.configure, value=progress)
                self.safe_ui(self.overall_status.config, text=f"📥 Đang tải {progress}/{total} video...")
            
            self.safe_ui(self.overall_status.config, text=f"🎉 Hoàn thành! {done}/{total} video")
            self.safe_ui(self.current_status.config, text="")
            self.safe_ui(self.current_progress.configure, value=0)
            self.safe_ui(self.log, f"🎉 Xong! {done}/{total} video về {download_path}")
            messagebox.showinfo("🎉 Hoàn thành", f"Đã tải {done}/{total} video Shorts thành công!")
        
        threading.Thread(target=download_task, daemon=True).start()
    
    def download_all(self):
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
