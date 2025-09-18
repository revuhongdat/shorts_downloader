import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import yt_dlp
import os
from datetime import datetime, timedelta
import threading

class ShortsDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Shorts YouTube Downloader By Dat0o")  # giữ nguyên title
        self.root.geometry("1100x840")
        
        self.items = []            # danh sách gốc (YouTube Shorts hoặc TikTok videos)
        self.filtered_items = []   # danh sách đang hiển thị (sau khi search)
        self.download_path = "./shorts_downloaded"
        self.cookies_path = ""     # tùy chọn
        
        self.setup_ui()
        self.configure_tree_style()
    
    # ========================= UI helpers (thread-safe) =========================
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
    
    # ========================= UI layout =========================
    def setup_ui(self):
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # --- Hàng 1: Kênh + Cài đặt (cùng dòng) ---
        top_row = tk.Frame(main)
        top_row.pack(fill=tk.X, pady=(0, 10))
        
        # Cột trái: Link (YouTube / TikTok)
        url_frame = tk.LabelFrame(top_row, text="📺 Kênh / Hồ sơ", font=('Arial', 10, 'bold'), padx=10, pady=8)
        url_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        tk.Label(url_frame, text="Dán link YouTube (kênh @/channel) hoặc TikTok (@username / link profile):") \
            .pack(anchor=tk.W, pady=(0, 5))
        self.link_var = tk.StringVar()
        tk.Entry(url_frame, textvariable=self.link_var, font=('Arial', 10)).pack(fill=tk.X)
        
        # Cột phải: Cài đặt
        settings_frame = tk.LabelFrame(top_row, text="⚙️ Cài đặt", font=('Arial', 10, 'bold'), padx=10, pady=8)
        settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))
        
        # Thư mục tải
        path_row = tk.Frame(settings_frame); path_row.pack(fill=tk.X, pady=2)
        tk.Label(path_row, text="📁 Thư mục:", width=12, anchor='w').pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.download_path)
        tk.Entry(path_row, textvariable=self.path_var, font=('Arial', 9)) \
            .pack(side=tk.LEFT, padx=(2, 5), fill=tk.X, expand=True)
        tk.Button(path_row, text="...", command=self.choose_directory, width=3, font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Cookies (tuỳ chọn)
        cookie_row = tk.Frame(settings_frame); cookie_row.pack(fill=tk.X, pady=(8,2))
        tk.Label(cookie_row, text="🍪 Cookies:", width=12, anchor='w').pack(side=tk.LEFT)
        self.cookies_var = tk.StringVar(value="")
        tk.Entry(cookie_row, textvariable=self.cookies_var, font=('Arial', 9)) \
            .pack(side=tk.LEFT, padx=(2,5), fill=tk.X, expand=True)
        tk.Button(cookie_row, text="Chọn", command=self.choose_cookies, width=6).pack(side=tk.LEFT)
        tk.Label(settings_frame, text="(Tuỳ chọn, hữu ích cho TikTok/YouTube khi bị hạn chế)", fg="#666", font=('Arial', 8)) \
            .pack(anchor='w', pady=(4,0))
        
        # --- Bộ lọc ngày (Từ ngày – Đến ngày) ---
        date_row = tk.LabelFrame(main, text="📅 Khoảng thời gian", font=('Arial', 10, 'bold'), padx=10, pady=8)
        date_row.pack(fill=tk.X, pady=(0, 10))
        dline = tk.Frame(date_row); dline.pack(fill=tk.X)
        tk.Label(dline, text="Từ ngày:", width=8, anchor='w').pack(side=tk.LEFT)
        self.from_date_var = tk.StringVar(value="")
        tk.Entry(dline, textvariable=self.from_date_var, width=12).pack(side=tk.LEFT, padx=(2, 12))
        tk.Label(dline, text="Đến ngày:", width=9, anchor='w').pack(side=tk.LEFT)
        self.to_date_var = tk.StringVar(value="")
        tk.Entry(dline, textvariable=self.to_date_var, width=12).pack(side=tk.LEFT, padx=(2, 12))
        tk.Label(dline, text="(dd/mm/yyyy) • Để trống = không giới hạn", font=('Arial', 8), fg='#666').pack(side=tk.LEFT)
        
        # NEW: checkbox bao gồm video không có ngày
        self.include_nodate_var = tk.BooleanVar(value=False)
        nodate_row = tk.Frame(date_row); nodate_row.pack(fill=tk.X, pady=(6,0))
        tk.Checkbutton(nodate_row, text="Bao gồm video KHÔNG có ngày (khi lọc)",
                       variable=self.include_nodate_var).pack(anchor='w')
        
        # --- Hàng 2: Điều khiển + Tìm kiếm (cùng dòng) ---
        second_row = tk.Frame(main)
        second_row.pack(fill=tk.X, pady=(0, 10))
        
        control_frame = tk.LabelFrame(second_row, text="🎮 Điều khiển", font=('Arial', 10, 'bold'), padx=10, pady=8)
        control_frame.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=(0,6))
        ctrl = tk.Frame(control_frame); ctrl.pack(fill=tk.X)
        tk.Button(ctrl, text="📋 Lấy danh sách",
                  command=self.get_list, width=16, bg='#4CAF50', fg='white',
                  font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(ctrl, text="💾 Tải tất cả",
                  command=self.download_all, width=12, bg='#2196F3', fg='white',
                  font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.videos_count_label = tk.Label(ctrl, text="", font=('Arial', 9), fg='#666')
        self.videos_count_label.pack(side=tk.LEFT, padx=(12,0))
        
        range_row = tk.Frame(control_frame); range_row.pack(fill=tk.X, pady=(8, 2))
        tk.Label(range_row, text="📊 Tải theo khoảng:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        tk.Label(range_row, text="Từ số:").pack(side=tk.LEFT, padx=(12, 5))
        self.start_var = tk.StringVar(value="1")
        tk.Entry(range_row, textvariable=self.start_var, width=6, justify='center').pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(range_row, text="đến số:").pack(side=tk.LEFT, padx=(0, 5))
        self.end_var = tk.StringVar(value="10")
        tk.Entry(range_row, textvariable=self.end_var, width=6, justify='center').pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(range_row, text="▶️ Tải theo lựa chọn",
                  command=self.download_range, width=16,
                  bg='#FF9800', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        search_frame = tk.LabelFrame(second_row, text="🔎 Tìm theo tiêu đề/mô tả", font=('Arial', 10, 'bold'), padx=10, pady=8)
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6,0))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        search_entry.bind("<Return>", lambda e: self.on_search())
        tk.Button(search_frame, text="Tìm", width=10, command=self.on_search).pack(side=tk.LEFT, padx=(0,6))
        tk.Button(search_frame, text="Xóa", width=10, command=self.on_clear_search).pack(side=tk.LEFT)
        
        # --- Tiến trình ---
        progress_frame = tk.LabelFrame(main, text="📈 Tiến trình", font=('Arial', 10, 'bold'), padx=10, pady=8)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(progress_frame, text="Tổng thể:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        overall_container = tk.Frame(progress_frame, height=25)
        overall_container.pack(fill=tk.X, pady=(2, 5)); overall_container.pack_propagate(False)
        self.overall_progress = ttk.Progressbar(overall_container, mode='determinate',
                                                style="Large.Horizontal.TProgressbar")
        self.overall_progress.pack(fill=tk.BOTH, expand=True, pady=3)
        self.overall_status = tk.Label(progress_frame, text="Sẵn sàng", anchor=tk.W, font=('Arial', 9))
        self.overall_status.pack(anchor=tk.W)
        
        tk.Label(progress_frame, text="Video hiện tại:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(8, 0))
        current_container = tk.Frame(progress_frame, height=20)
        current_container.pack(fill=tk.X, pady=(2, 5)); current_container.pack_propagate(False)
        self.current_progress = ttk.Progressbar(current_container, mode='determinate',
                                                style="Small.Horizontal.TProgressbar")
        self.current_progress.pack(fill=tk.BOTH, expand=True, pady=2)
        self.current_status = tk.Label(progress_frame, text="", anchor=tk.W, font=('Arial', 8))
        self.current_status.pack(anchor=tk.W)
        
        # --- Danh sách ---
        list_frame = tk.LabelFrame(main, text="📋 Danh sách Video", font=('Arial', 10, 'bold'), padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tree_frame = tk.Frame(list_frame, relief=tk.SUNKEN, borderwidth=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('STT', 'Nền tảng', 'Tiêu đề/Mô tả', 'Thời lượng', 'Ngày', 'Trạng thái')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8, style="Bordered.Treeview")
        self.tree.heading('STT', text='STT', anchor='center')
        self.tree.heading('Nền tảng', text='Nền tảng', anchor='center')
        self.tree.heading('Tiêu đề/Mô tả', text='Tiêu đề/Mô tả', anchor='w')
        self.tree.heading('Thời lượng', text='Thời lượng (s)', anchor='center')
        self.tree.heading('Ngày', text='Ngày', anchor='center')
        self.tree.heading('Trạng thái', text='Trạng thái', anchor='center')
        self.tree.column('STT', width=50, anchor='center', minwidth=50)
        self.tree.column('Nền tảng', width=90, anchor='center', minwidth=70)
        self.tree.column('Tiêu đề/Mô tả', width=430, anchor='w', minwidth=260)
        self.tree.column('Thời lượng', width=110, anchor='center', minwidth=80)
        self.tree.column('Ngày', width=120, anchor='center', minwidth=100)
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
        
        # --- Log ---
        log_frame = tk.LabelFrame(main, text="📝 Nhật ký hoạt động", font=('Arial', 10, 'bold'), padx=5, pady=5)
        log_frame.pack(fill=tk.X)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80, font=('Consolas', 9), bg='#f8f9fa')
        self.log_text.pack(fill=tk.BOTH, padx=5, pady=5)
    
    # ========================= Utils & platform detect =========================
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
    
    def detect_platform(self, url: str) -> str:
        url = (url or "").lower()
        if "tiktok.com" in url:
            return "tiktok"
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        return "unknown"
    
    # --------- Date filter helpers ---------
    def parse_date(self, s):
        s = (s or "").strip()
        if not s:
            return None
        try:
            return datetime.strptime(s, "%d/%m/%Y")
        except ValueError:
            return None
    
    def get_date_range(self):
        """Trả về (from_dt, to_dt) hoặc (None, None) nếu bỏ trống cả hai; raise nếu định dạng lỗi."""
        from_dt = self.parse_date(self.from_date_var.get())
        to_dt = self.parse_date(self.to_date_var.get())
        if self.from_date_var.get().strip() == "" and self.to_date_var.get().strip() == "":
            return None, None  # không lọc
        if (self.from_date_var.get().strip() != "" and from_dt is None) or (self.to_date_var.get().strip() != "" and to_dt is None):
            raise ValueError("Định dạng ngày không hợp lệ! Vui lòng dùng dd/mm/yyyy.")
        # nếu chỉ có 1 đầu mút, đặt đầu kia mở rộng
        if from_dt is None:
            from_dt = datetime(1970, 1, 1)
        if to_dt is None:
            to_dt = datetime(2100, 1, 1)
        # inclusive đến cuối ngày
        to_dt = to_dt.replace(hour=23, minute=59, second=59)
        if from_dt > to_dt:
            raise ValueError("Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.")
        return from_dt, to_dt
    
    def is_in_range(self, up_dt, from_dt, to_dt):
        """Áp dụng checkbox 'bao gồm video không có ngày' khi đang lọc."""
        if from_dt is None and to_dt is None:
            return True
        if up_dt is None:
            return self.include_nodate_var.get()  # nếu bật → cho qua
        return from_dt <= up_dt <= to_dt
    
    # ========================= Get lists =========================
    def get_list(self):
        url = self.link_var.get().strip()
        platform = self.detect_platform(url)
        if platform == "unknown":
            messagebox.showwarning("❌ Lỗi", "Vui lòng nhập link kênh YouTube (@/channel) hoặc TikTok (@username).")
            return
        
        # Lấy khoảng ngày (nếu có)
        try:
            from_dt, to_dt = self.get_date_range()
            if from_dt and to_dt:
                more = " • Bao gồm KHÔNG ngày" if self.include_nodate_var.get() else ""
                self.safe_ui(self.log, f"🔍 Lọc từ {from_dt.strftime('%d/%m/%Y')} đến {to_dt.strftime('%d/%m/%Y')}{more}")
            else:
                self.safe_ui(self.log, "🔍 Không lọc ngày (lấy tất cả)")
        except ValueError as e:
            messagebox.showwarning("❌ Lỗi", str(e))
            return
        
        self.safe_ui(self.overall_status.config, text="🔍 Đang quét...")
        self.safe_ui(self.videos_count_label.config, text="")
        
        def fetch():
            try:
                self.safe_ui(lambda: [self.tree.delete(i) for i in self.tree.get_children()])
                self.items = []
                self.filtered_items = []
                
                if platform == "youtube":
                    entries = self.fetch_youtube_shorts(url, limit=5000)
                else:
                    entries = self.fetch_tiktok_profile(url, limit=5000)
                
                if not entries:
                    self.safe_ui(self.log, "❌ Không thể lấy danh sách video!")
                    messagebox.showerror("❌ Lỗi", "Không thể lấy danh sách video!")
                    return
                
                data = []
                checked = 0
                kept = 0
                for v in entries:
                    if not v:
                        continue
                    checked += 1
                    if checked % 50 == 0:
                        self.safe_ui(self.log, f"📊 Phân tích {checked}/{len(entries)}...")
                    
                    try:
                        row = self.normalize_item(v, platform)
                        if not row:
                            continue
                        # Áp dụng lọc ngày (nếu có)
                        up_dt = None
                        if row['upload_date'] and row['upload_date'] != '00000000':
                            try:
                                up_dt = datetime.strptime(row['upload_date'], "%Y%m%d")
                            except Exception:
                                up_dt = None
                        if self.is_in_range(up_dt, from_dt, to_dt):
                            data.append(row); kept += 1
                    except Exception as e:
                        self.safe_ui(self.log, f"⚠️ Lỗi khi phân tích: {e}")
                        continue
                
                # Sắp xếp: có ngày trước, sau đó giảm dần
                data.sort(key=lambda x: (x['upload_date'] == '00000000', x['upload_date']), reverse=True)
                self.items = data
                self.filtered_items = data[:]
                self.safe_ui(self.render_tree, self.filtered_items)
                
                self.safe_ui(self.log, f"🎉 Hoàn thành! Tìm thấy {kept}/{checked} video hợp lệ.")
                self.safe_ui(self.overall_status.config, text=f"✅ Tìm thấy {len(data)} video")
                self.safe_ui(self.videos_count_label.config, text=f"📊 Tổng hiển thị: {len(self.filtered_items)}")
                if data:
                    self.safe_ui(self.end_var.set, str(len(self.filtered_items)))
                
                # Ghi chú cho YouTube nếu lọc ngày
                if platform == "youtube" and (from_dt or to_dt) and not self.include_nodate_var.get():
                    self.safe_ui(self.log, "ℹ️ YouTube Shorts đôi khi thiếu ngày trong listing; video thiếu ngày đã bị loại. Bật checkbox để giữ chúng.")
            
            except Exception as e:
                self.safe_ui(self.log, f"❌ Lỗi khi lấy danh sách: {e}")
                messagebox.showerror("❌ Lỗi", f"Lỗi khi lấy danh sách: {e}")
                self.safe_ui(self.overall_status.config, text="❌ Lỗi")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def fetch_youtube_shorts(self, channel_url, limit=5000):
        """Lấy tab Shorts của kênh YouTube (extract_flat)."""
        ydl_opts = {
            'quiet': True, 'no_warnings': True,
            'extract_flat': True, 'playlistend': limit,
            'ignoreerrors': True, 'retries': 5,
            'extractor_args': {'youtube': {'tab': ['shorts']}}
        }
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = channel_url.rstrip('/')
            if not url.endswith('/shorts'):
                url += '/shorts'
            info = ydl.extract_info(url, download=False)
            return info.get('entries', []) if info else []
    
    def fetch_tiktok_profile(self, profile_url, limit=5000):
        """Lấy toàn bộ video từ hồ sơ TikTok (@username)."""
        ydl_opts = {
            'quiet': True, 'no_warnings': True,
            'extract_flat': True, 'playlistend': limit,
            'ignoreerrors': True, 'retries': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.tiktok.com/'
            },
            # Ưu tiên luồng không watermark (nếu khả dụng)
            'extractor_args': {
                'tiktok': {'app_name': ['musically_go']}
            }
        }
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(profile_url, download=False)
            if not info:
                return []
            if 'entries' in info and isinstance(info['entries'], list):
                return info['entries']
            return []
    
    def normalize_item(self, v, platform):
        """Chuẩn hoá 1 item vào cấu trúc chung cho bảng & tải."""
        vid = v.get('id') or v.get('url') or ""
        if not vid:
            return None
        
        # Lấy ngày
        up_dt = None
        up_raw = v.get('upload_date')
        ts = v.get('timestamp') or v.get('release_timestamp')
        if ts:
            up_dt = datetime.fromtimestamp(ts)
            upload_date = up_dt.strftime('%Y%m%d'); formatted = up_dt.strftime('%d/%m/%Y')
        elif up_raw:
            try:
                up_dt = datetime.strptime(up_raw, "%Y%m%d")
                upload_date = up_raw; formatted = up_dt.strftime('%d/%m/%Y')
            except Exception:
                upload_date = '00000000'; formatted = '—'
        else:
            upload_date = '00000000'; formatted = '—'
        
        title = v.get('title') or v.get('description') or 'Untitled'
        duration = int(v.get('duration') or 0)
        
        if platform == "youtube":
            # id có thể là watch url khi extract_flat
            if isinstance(vid, str) and 'watch?v=' in vid:
                vid_clean = vid.split('watch?v=')[-1].split('&')[0]
            else:
                vid_clean = vid
            page_url = f"https://www.youtube.com/watch?v={vid_clean}"
            download_url = page_url
        else:  # tiktok
            page_url = v.get('url') or v.get('webpage_url') or vid
            if not str(page_url).startswith('http'):
                page_url = f"https://www.tiktok.com/{page_url.lstrip('/')}"
            download_url = page_url
        
        return {
            'platform': platform,
            'id': vid,
            'title': title,
            'duration': duration,
            'upload_date': upload_date,
            'formatted_date': formatted,
            'page_url': page_url,
            'download_url': download_url
        }
    
    # ---------- Render & Search ----------
    def render_tree(self, data_list):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, s in enumerate(data_list, 1):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            title = s['title'] if len(s['title']) <= 70 else s['title'][:70] + '...'
            self.tree.insert('', 'end',
                             values=(idx, s['platform'], title, s['duration'], s['formatted_date'], "Chưa tải"),
                             tags=(tag,))
        self.videos_count_label.config(text=f"📊 Hiển thị: {len(data_list)} / Tổng: {len(self.items)}")
        if data_list:
            self.end_var.set(str(len(data_list)))
    
    def on_search(self):
        kw = (self.search_var.get() or "").strip().lower()
        if not self.items:
            messagebox.showinfo("Thông báo", "Chưa có dữ liệu. Hãy bấm 'Lấy danh sách' trước.")
            return
        if kw == "":
            self.filtered_items = self.items[:]
        else:
            self.filtered_items = [v for v in self.items if kw in (v.get('title') or '').lower()]
        self.render_tree(self.filtered_items)
        self.log(f"🔎 Tìm '{kw}': {len(self.filtered_items)} kết quả")
    
    def on_clear_search(self):
        self.search_var.set("")
        self.filtered_items = self.items[:]
        self.render_tree(self.filtered_items)
        self.log("🧹 Đã xóa tìm kiếm. Hiển thị toàn bộ danh sách.")
    
    # ========================= Download =========================
    def get_download_format(self):
        # best video + best audio (yt-dlp sẽ tự merge)
        return "bv*+ba/best"
    
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                if d.get('total_bytes'):
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif d.get('total_bytes_estimate'):
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    percent = 0.0
                
                speed = d.get('speed') or 0
                speed_str = f"{speed/1024/1024:.1f} MB/s" if speed > 1024*1024 else f"{speed/1024:.1f} KB/s"
                
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                size_str = f"{downloaded/1024/1024:.1f} MB" if not total else f"{downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB"
                
                self.safe_ui(self.current_progress.configure, value=percent)
                self.safe_ui(self.current_status.config, text=f"📥 {percent:.1f}% - {speed_str} - {size_str}")
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.safe_ui(self.current_progress.configure, value=100)
            self.safe_ui(self.current_status.config, text="✅ Hoàn thành tải video")
    
    def update_tree_status(self, index, status):
        items = self.tree.get_children()
        if 0 <= index < len(items):
            item = items[index]
            values = list(self.tree.item(item)['values'])
            values[5] = status  # cột trạng thái
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
    
    def download_one(self, info, index, total_index):
        download_path = self.path_var.get().strip() or self.download_path
        fmt = self.get_download_format()
        outtmpl = f'{download_path}/%(upload_date,unknown)s_%(title).150B.%(ext)s'
        
        http_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.tiktok.com/' if info['platform'] == 'tiktok' else 'https://www.youtube.com/'
        }
        
        ydl_opts = {
            'format': fmt,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'http_headers': http_headers,
            'progress_hooks': [self.progress_hook],
            'noprogress': True,
            'retries': 5,
            'fragment_retries': 5,
            'concurrent_fragment_downloads': 4,
            'ignoreerrors': False,
            
            # Luôn xuất MP4 (ghép audio + tránh lỗi 0xc00d5212)
            'merge_output_format': 'mp4',
            'recodevideo': 'mp4',
            'postprocessor_args': [
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart'
            ],
            # 'ffmpeg_location': r'C:\ffmpeg\bin',  # bật nếu cần
        }
        
        # Ưu tiên no-watermark cho TikTok
        if info['platform'] == 'tiktok':
            ydl_opts.setdefault('extractor_args', {})
            ydl_opts['extractor_args'].setdefault('tiktok', {})
            ydl_opts['extractor_args']['tiktok']['app_name'] = ['musically_go']
        
        if self.cookies_path and os.path.exists(self.cookies_path):
            ydl_opts['cookiefile'] = self.cookies_path
        
        try:
            self.safe_ui(self.update_tree_status, index, "Đang tải...")
            short_title = (info['title'][:40] + '...') if len(info['title']) > 40 else info['title']
            self.safe_ui(self.current_status.config, text=f"📥 Đang tải: {short_title}")
            self.safe_ui(self.current_progress.configure, value=0)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.safe_ui(self.log, f"📥 [{total_index}] {info['platform'].upper()} — {info['title']}")
                ydl.download([info['download_url']])
            
            self.safe_ui(self.update_tree_status, index, "Hoàn thành")
            self.safe_ui(self.log, f"✅ [{total_index}] Hoàn thành: {info['title']}")
            return True
        
        except Exception as e:
            self.safe_ui(self.update_tree_status, index, "Lỗi")
            self.safe_ui(self.log, f"❌ [{total_index}] Lỗi: {e}")
            return False
    
    def download_range(self):
        if not self.filtered_items:
            messagebox.showwarning("❌ Lỗi", "Chưa có danh sách để tải (hãy Lấy danh sách hoặc Xóa tìm kiếm).")
            return
        try:
            start_idx = int(self.start_var.get()) - 1
            end_idx = int(self.end_var.get())
            if start_idx < 0 or end_idx > len(self.filtered_items) or start_idx >= end_idx:
                messagebox.showwarning("❌ Lỗi", "Số thứ tự không hợp lệ!")
                return
        except ValueError:
            messagebox.showwarning("❌ Lỗi", "Vui lòng nhập số hợp lệ!")
            return
        
        def task():
            download_path = self.path_var.get().strip() or self.download_path
            os.makedirs(download_path, exist_ok=True)
            
            total = end_idx - start_idx
            done = 0
            self.safe_ui(self.overall_progress.configure, maximum=total, value=0)
            
            self.safe_ui(self.log, f"🚀 Bắt đầu tải {total} video theo danh sách đang hiển thị")
            self.safe_ui(self.overall_status.config, text=f"📥 Đang tải 0/{total} video...")
            
            for i in range(start_idx, end_idx):
                if self.download_one(self.filtered_items[i], i, i + 1):
                    done += 1
                progress = i - start_idx + 1
                self.safe_ui(self.overall_progress.configure, value=progress)
                self.safe_ui(self.overall_status.config, text=f"📥 Đang tải {progress}/{total} video...")
            
            self.safe_ui(self.overall_status.config, text=f"🎉 Hoàn thành! {done}/{total} video")
            self.safe_ui(self.current_status.config, text="")
            self.safe_ui(self.current_progress.configure, value=0)
            self.safe_ui(self.log, f"🎉 Xong! {done}/{total} video về {download_path}")
            messagebox.showinfo("🎉 Hoàn thành", f"Đã tải {done}/{total} video thành công!")
        
        threading.Thread(target=task, daemon=True).start()
    
    def download_all(self):
        if not self.filtered_items:
            messagebox.showwarning("❌ Lỗi", "Chưa có danh sách để tải (hãy Lấy danh sách hoặc Xóa tìm kiếm).")
            return
        self.start_var.set("1")
        self.end_var.set(str(len(self.filtered_items)))
        self.download_range()


if __name__ == "__main__":
    root = tk.Tk()
    app = ShortsDownloader(root)
    root.mainloop()
