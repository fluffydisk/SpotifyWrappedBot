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
            self.login_btn = ctk.CTkButton(
                self.profile_wrapper,
                text="Log In",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#FFFFFF",
                hover_color="#F0F0F0",
                text_color="#000000",
                height=32,
                width=80,
                corner_radius=16,
                command=self.on_launch_click
            )
            self.login_btn.pack()
            self.profile_menu_visible = False
        else:
            self.login_btn = None
            name = profile_data.get("name", "User")
            avatar_url = profile_data.get("avatar")
            
            # 1. Profile Card (Clickable)
            self.profile_card = ctk.CTkFrame(
                self.profile_wrapper, 
                fg_color=COLORS["bg_card"], 
                height=42, 
                corner_radius=21, 
                cursor="hand2",
                border_width=1,
                border_color=COLORS["border"]
            )
            self.profile_card.pack(side="top", anchor="e")
            
            # Avatar (Right)
            if avatar_url:
                try:
                    response = requests.get(avatar_url, timeout=5)
                    img_data = Image.open(BytesIO(response.content))
                    avatar_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(30, 30))
                    avatar_lbl = ctk.CTkLabel(self.profile_card, image=avatar_img, text="")
                except:
                    avatar_lbl = ctk.CTkLabel(
                        self.profile_card, 
                        text=name[0].upper(), 
                        fg_color=COLORS["accent_primary"], 
                        text_color=COLORS["bg_dark"], 
                        width=30, 
                        height=30, 
                        corner_radius=15,
                        font=ctk.CTkFont(size=14, weight="bold")
                    )
            else:
                avatar_lbl = ctk.CTkLabel(
                    self.profile_card, 
                    text=name[0].upper(), 
                    fg_color=COLORS["accent_primary"], 
                    text_color=COLORS["bg_dark"], 
                    width=30, 
                    height=30, 
                    corner_radius=15,
                    font=ctk.CTkFont(size=14, weight="bold")
                )
            
            avatar_lbl.pack(side="right", padx=(5, 6), pady=5)
            
            # Name (Left)
            name_lbl = ctk.CTkLabel(
                self.profile_card, 
                text=name, 
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), 
                text_color=COLORS["text_primary"]
            )
            name_lbl.pack(side="right", padx=(12, 5))
            
            # Bind click events
            for widget in [self.profile_card, name_lbl, avatar_lbl]:
                widget.bind("<Button-1>", lambda e: self._toggle_profile_menu())
                widget.bind("<Enter>", lambda e: self.profile_card.configure(fg_color=COLORS["border"], border_color=COLORS["text_secondary"]))
                widget.bind("<Leave>", lambda e: self.profile_card.configure(fg_color=COLORS["bg_card"], border_color=COLORS["border"]))

            # 2. Dropdown Menu (Hidden by default)
            self.profile_menu = ctk.CTkFrame(
                self.main_frame, 
                fg_color=COLORS["bg_card"], 
                border_width=1, 
                border_color=COLORS["border"], 
                corner_radius=8,
                width=140,
                height=45
            )
            self.profile_menu.pack_propagate(False)
            self.profile_menu_visible = False
            
            # Logout option
            self.menu_logout_btn = ctk.CTkButton(
                self.profile_menu,
                text="  Log out",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLORS["danger"],
                text_color=COLORS["text_primary"],
                anchor="w",
                height=35,
                corner_radius=4,
                command=self.on_logout_click
            )
            self.menu_logout_btn.pack(fill="x", padx=5, pady=5)

    def _toggle_profile_menu(self):
        """Toggles the visibility of the profile dropdown menu."""
        if not hasattr(self, 'profile_menu'): return
        
        if self.profile_menu_visible:
            self.profile_menu.place_forget()
            self.profile_menu_visible = False
        else:
            # Position relative to the window top-right
            # self.profile_wrapper is at top-right
            self.profile_menu.place(relx=0.98, y=65, anchor="ne")
            self.profile_menu.lift()
            self.profile_menu_visible = True

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
        """Builds the action buttons (Start/Stop) with modern styling."""
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Configure grid/columns
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
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
        self.start_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
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
        self.stop_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

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
        """Handle login button click - open cookie import dialog or auto-login"""
        # Initialize bot if needed
        if not self.bot:
            self.bot = SpotifyBot({"profile_dir": "spotify_profile"})
        
        # Check if cookies already exist
        if self.bot.has_valid_session():
            Logger.info("Existing session found. Auto-logging in...")
            self._set_status("Logged In ✓", COLORS["accent_primary"])
            self.logged_in = True
            if hasattr(self, 'login_btn') and self.login_btn:
                # Update profile UI with default data
                self._update_profile_ui({"name": "Spotify User", "avatar": None})
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
            return
        
        # No cookies - open import dialog
        from src.ui.cookie_dialog import CookieDialog
        
        dialog = CookieDialog(self, on_success=self._on_cookies_imported)
        # Dialog is modal, wait for it to close
    
    def _on_cookies_imported(self, cookies):
        """Callback when cookies are successfully imported"""
        try:
            # Save cookies
            BrowserManager.save_cookies(cookies, "spotify_profile")
            
            # Update UI
            Logger.info("Cookies imported successfully. Session ready!")
            self.logged_in = True
            self._set_status("Logged In ✓", COLORS["accent_primary"])
            
            # Update profile UI
            self._update_profile_ui({"name": "Spotify User", "avatar": None})
            
            # Enable buttons
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
            
        except Exception as e:
            Logger.error(f"Failed to save cookies: {e}")
            self._set_status("Cookie Save Failed", COLORS["danger"])

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
        else:
            self._set_status("Stopped", COLORS["text_muted"])
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")

    def on_logout_click(self):
        """Clears the session and returns to login state."""
        import shutil
        import os
        
        if self.bot and self.bot.running:
            self.bot.stop_session()
        
        # Reset state
        self.logged_in = False
        if self.bot:
            self.bot.profile_info = None
            
        # UI Cleanup
        if hasattr(self, 'profile_menu') and self.profile_menu:
            self.profile_menu.place_forget()
            
        self._update_profile_ui(None)
        self._set_status("Logged Out", COLORS["text_muted"])
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        
        # Delete only cookies.json (not entire profile directory)
        try:
            cookie_file = os.path.join("spotify_profile", "cookies.json")
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
                Logger.info("Logged out and session cleared.")
            else:
                Logger.info("Logged out.")
        except Exception as e:
            Logger.debug(f"Cookie cleanup failed: {e}")
            Logger.info("Logged out.")
