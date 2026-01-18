import customtkinter as ctk
import threading
import os
from src.auth.license_manager import LicenseManager
from src.core.bot_engine import SpotifyBot
from src.core.browser_mgr import BrowserManager
from src.utils.logger import Logger
from PIL import Image, ImageTk
import requests
from io import BytesIO

# ══════════════════════════════════════════════════════════════════════════════
# THEME CONFIGURATION - Modern Dark Mode
# ══════════════════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Color Palette
COLORS = {
    "bg_dark": "#0D0D0D",
    "bg_card": "#1A1A1A",
    "bg_input": "#252525",
    "accent_primary": "#1DB954",      # Spotify Green
    "accent_secondary": "#1ED760",
    "accent_gradient_start": "#1DB954",
    "accent_gradient_end": "#1ED760",
    "danger": "#E63946",
    "danger_hover": "#FF4D5A",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B3B3B3",
    "text_muted": "#6B6B6B",
    "border": "#333333",
    "border_focus": "#1DB954",
    "terminal_bg": "#0A0A0A",
    "terminal_text": "#00FF41",
}

class MainWindow(ctk.CTk):
    """
    Modern, Professional UI for the Spotify Automation Bot.
    Dark theme with Spotify-inspired green accents.
    """
    def __init__(self):
        super().__init__()
        
        # Window Configuration
        self.title("Spotify Wrapped Bot")
        self.geometry("700x650")
        self.configure(fg_color=COLORS["bg_dark"])
        self.resizable(False, False)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")
        
        # State
        self.auth_manager = LicenseManager()
        self.bot = None
        self.logged_in = False  # Track if user has logged in this session
        
        self._build_ui()

    def _build_ui(self):
        """Constructs the entire UI layout."""
        
        # ── Main Container ───────────────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=25)

        # ── Header Section ───────────────────────────────────────────────────
        self._build_header()
        
        # ── Input Section ────────────────────────────────────────────────────
        self._build_inputs()
        
        # ── Status Section ───────────────────────────────────────────────────
        self._build_status()
        
        # ── Button Section ───────────────────────────────────────────────────
        self._build_buttons()
        
        # ── Log/Terminal Section ─────────────────────────────────────────────
        self._build_terminal()
        
        # Connect Logger
        Logger.add_callback(self._append_log)

    def _build_header(self):
        """Builds the header with title, subtitle, and profile widget."""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 25))
        
        # Profile Wrapper (Top Right)
        self.profile_wrapper = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.profile_wrapper.place(relx=1.0, x=0, y=0, anchor="ne")
        self._update_profile_ui(None)
        
        # Title with gradient effect
        title_label = ctk.CTkLabel(
            header_frame, 
            text="⚡ Spotify Wrapped Bot",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor="center")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame, 
            text="Pure Automation Engine",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_muted"]
        )
        subtitle_label.pack(anchor="center", pady=(2, 0))

    def _update_profile_ui(self, profile_data=None):
        """Updates the top-right profile widget based on login state."""
        # Clear existing widgets in wrapper
        for child in self.profile_wrapper.winfo_children():
            child.destroy()
            
        if not profile_data:
            # Show Spotify-style Login Button
            login_btn = ctk.CTkButton(
                self.profile_wrapper,
                text="Log In",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#FFFFFF",     # Spotify White
                hover_color="#F0F0F0",
                text_color="#000000",   # Black text
                height=32,
                width=80,
                corner_radius=16,       # Pill shape
                command=self.on_launch_click
            )
            login_btn.pack()
        else:
            # Show User Profile
            name = profile_data.get("name", "User")
            avatar_url = profile_data.get("avatar")
            
            # Profile Container
            profile_card = ctk.CTkFrame(self.profile_wrapper, fg_color=COLORS["bg_card"], height=40, corner_radius=20)
            profile_card.pack(padx=2, pady=2)
            
            # Avatar
            if avatar_url:
                try:
                    response = requests.get(avatar_url, timeout=5)
                    img_data = Image.open(BytesIO(response.content))
                    # Circular crop (simplified by customtkinter rounding if we use an image)
                    avatar_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(30, 30))
                    avatar_lbl = ctk.CTkLabel(profile_card, image=avatar_img, text="")
                    avatar_lbl.pack(side="right", padx=(5, 5))
                except:
                    # Fallback icon or initial
                    avatar_lbl = ctk.CTkLabel(profile_card, text=name[0].upper(), fg_color=COLORS["accent_primary"], text_color=COLORS["bg_dark"], width=30, height=30, corner_radius=15)
                    avatar_lbl.pack(side="right", padx=(5, 5))
            else:
                avatar_lbl = ctk.CTkLabel(profile_card, text=name[0].upper(), fg_color=COLORS["accent_primary"], text_color=COLORS["bg_dark"], width=30, height=30, corner_radius=15)
                avatar_lbl.pack(side="right", padx=(5, 5))
                
            # Name
            name_lbl = ctk.CTkLabel(profile_card, text=name, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_primary"])
            name_lbl.pack(side="left", padx=(15, 5))

    def _build_inputs(self):
        """Builds the styled input fields."""
        inputs_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        inputs_frame.pack(fill="x", pady=(0, 20))
        
        inner_padding = ctk.CTkFrame(inputs_frame, fg_color="transparent")
        inner_padding.pack(fill="x", padx=20, pady=20)

        # License Key Input
        license_label = ctk.CTkLabel(
            inner_padding, 
            text="🔑  License Key",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        license_label.pack(fill="x", pady=(0, 6))
        
        self.license_entry = ctk.CTkEntry(
            inner_padding,
            placeholder_text="Enter your license key...",
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13)
        )
        self.license_entry.pack(fill="x", pady=(0, 16))

        # Target URL Input
        url_label = ctk.CTkLabel(
            inner_padding, 
            text="🎵  Target Playlist / Song URL",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        url_label.pack(fill="x", pady=(0, 6))
        
        self.url_entry = ctk.CTkEntry(
            inner_padding,
            placeholder_text="https://open.spotify.com/track/...",
            height=44,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.pack(fill="x")
        
        # Bind keyboard shortcuts
        self._bind_shortcuts(self.license_entry)
        self._bind_shortcuts(self.url_entry)

    def _build_status(self):
        """Builds the status indicator section."""
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 16))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="● Ready",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(anchor="center")

    def _build_buttons(self):
        """Builds the action buttons with modern styling."""
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Configure grid for equal spacing
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)
        
        # Launch Browser Button (Primary Action)
        self.launch_btn = ctk.CTkButton(
            buttons_frame,
            text="🚀  Launch Browser",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=48,
            corner_radius=10,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_secondary"],
            text_color=COLORS["bg_dark"],
            command=self.on_launch_click
        )
        self.launch_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
        # Start Bot Button
        self.start_btn = ctk.CTkButton(
            buttons_frame,
            text="▶  Start Bot",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=48,
            corner_radius=10,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["accent_primary"],
            text_color=COLORS["accent_primary"],
            command=self.on_start_click,
            state="disabled"
        )
        self.start_btn.grid(row=0, column=1, padx=8, sticky="ew")
        
        # Stop Button (Danger)
        self.stop_btn = ctk.CTkButton(
            buttons_frame,
            text="⏹  Stop",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=48,
            corner_radius=10,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            text_color=COLORS["text_primary"],
            command=self.on_stop_click,
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=2, padx=(8, 0), sticky="ew")

    def _build_terminal(self):
        """Builds the terminal-like log area."""
        # Terminal Header
        terminal_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        terminal_header.pack(fill="x", pady=(0, 6))
        
        terminal_title = ctk.CTkLabel(
            terminal_header,
            text="📟  Activity Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_secondary"]
        )
        terminal_title.pack(anchor="w")
        
        # Terminal Body
        terminal_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["terminal_bg"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        terminal_frame.pack(fill="both", expand=True)
        
        self.log_box = ctk.CTkTextbox(
            terminal_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="transparent",
            text_color=COLORS["terminal_text"],
            corner_radius=0,
            wrap="word",
            activate_scrollbars=True
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=12)
        self.log_box.configure(state="disabled")

    def _bind_shortcuts(self, widget):
        """Adds standard keyboard shortcuts to entry fields."""
        def select_all(event):
            widget.select_range(0, 'end')
            widget.icursor('end')
            return 'break'
            
        def paste(event):
            try:
                widget.insert('insert', self.clipboard_get())
            except: pass
            return 'break'
            
        def copy(event):
            try:
                self.clipboard_clear()
                self.clipboard_append(widget.get())
            except: pass
            return 'break'

        widget.bind("<Control-a>", select_all)
        widget.bind("<Control-v>", paste)
        widget.bind("<Control-c>", copy)

    def _append_log(self, msg):
        """Thread-safe log appender."""
        def _update():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"{msg}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _update)

    def _set_status(self, text, color=None):
        """Updates the status label."""
        if color is None:
            color = COLORS["text_muted"]
        self.status_label.configure(text=f"● {text}", text_color=color)

    # ══════════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════════════
    def on_launch_click(self):
        self._set_status("Checking browsers...", COLORS["text_secondary"])
        self.launch_btn.configure(state="disabled")
        threading.Thread(target=self._login_task, daemon=True).start()

    def _login_task(self):
        try:
            # 1. Ensure browser is available
            if not BrowserManager.ensure_browser_installed():
                Logger.error("No browser found. Install Chrome or Firefox.")
                self.after(0, lambda: self._set_status("No Browser Found", COLORS["danger"]))
                self.after(0, lambda: self.launch_btn.configure(state="normal"))
                return

            if not self.bot:
                self.bot = SpotifyBot({"profile_dir": "spotify_profile"})
            
            # 2. Launch Controlled Login
            self.after(0, lambda: self._set_status("Logging in...", COLORS["accent_primary"]))
            
            success, profile_data = self.bot.launch_native_login()
            if success:
                Logger.info("Login successful. Ready to start bot.")
                self.logged_in = True  # Mark as logged in
                self.after(0, lambda: self._update_profile_ui(profile_data))
                self.after(0, lambda: self._set_status("Logged In ✓", COLORS["accent_primary"]))
                self.after(0, lambda: self.start_btn.configure(state="normal"))
                self.after(0, lambda: self.stop_btn.configure(state="normal"))
            else:
                self.after(0, lambda: self._set_status("Login Failed", COLORS["danger"]))
                self.after(0, lambda: self.launch_btn.configure(state="normal"))

        except Exception as e:
            Logger.error(f"Login error: {e}")
            self.after(0, lambda: self.launch_btn.configure(state="normal"))
            self.after(0, lambda: self._set_status("Error", COLORS["danger"]))

    def on_start_click(self):
        url = self.url_entry.get()
        if not url:
            Logger.error("Please enter a target URL.")
            return
            
        self.start_btn.configure(state="disabled")
        self._set_status("Running", COLORS["accent_primary"])
        threading.Thread(target=self._run_headless_task, args=(url,), daemon=True).start()

    def _run_headless_task(self, url):
        try:
            self.bot.launch_browser(headless=True)
            self.bot.start_loop(url)
        except Exception as e:
            Logger.error(f"Bot error: {e}")
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.after(0, lambda: self._set_status("Error", COLORS["danger"]))

    def on_stop_click(self):
        if self.bot:
            self.bot.stop_session()
        
        # If already logged in, allow restarting without re-login
        if self.logged_in:
            self._set_status("Stopped (Session Active)", COLORS["text_secondary"])
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
            # Keep launch_btn disabled since we're already logged in
            self.launch_btn.configure(state="disabled")
        else:
            self._set_status("Stopped", COLORS["text_muted"])
            self.launch_btn.configure(state="normal")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
