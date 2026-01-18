import customtkinter as ctk
import threading
import os
from src.auth.license_manager import LicenseManager
from src.core.bot_engine import SpotifyBot
from src.utils.logger import Logger

class MainWindow(ctk.CTk):
    """
    Simplified GUI for Pure Automation Flow.
    """
    def __init__(self):
        super().__init__()
        
        self.title("Spotify Wrapped Bot v2")
        self.geometry("600x550")
        
        self.auth_manager = LicenseManager()
        self.bot = None
        
        self.setup_ui()

    def setup_ui(self):
        # Title
        self.label = ctk.CTkLabel(self, text="Spotify Pure Automation", font=("Roboto", 24))
        self.label.pack(pady=20)

        # License (Always bypass in dev for now)
        self.license_entry = ctk.CTkEntry(self, placeholder_text="License Key", width=300)
        self.license_entry.pack(pady=5)

        # URL
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Target Playlist/Song URL", width=400)
        self.url_entry.pack(pady=10)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Status: Ready", text_color="gray")
        self.status_label.pack(pady=5)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=20)

        self.launch_btn = ctk.CTkButton(self.btn_frame, text="1. Launch Browser", command=self.on_launch_click)
        self.launch_btn.pack(side="left", padx=10)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="2. Start Bot", command=self.on_start_click, state="disabled")
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="Stop", command=self.on_stop_click, fg_color="red", state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        # Logs
        self.log_box = ctk.CTkTextbox(self, height=150, width=500)
        self.log_box.pack(pady=10)
        self.log_box.configure(state="disabled")

        Logger.add_callback(self.append_log)
        
        # Bind Shortcuts (Ctrl+A, Ctrl+C, Ctrl+V)
        self._bind_shortcuts(self.url_entry)
        self._bind_shortcuts(self.license_entry)

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

    def append_log(self, msg):
        def _update():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _update)

    def on_launch_click(self):
        self.status_label.configure(text="Status: Launching Login Window...", text_color="orange")
        self.launch_btn.configure(state="disabled")
        
        threading.Thread(target=self._login_task, daemon=True).start()

    def _login_task(self):
        try:
            if not self.bot:
                self.bot = SpotifyBot({"profile_dir": "spotify_profile"})
            
            # Use Native Login to bypass Google/Spotify detection
            self.bot.launch_native_login(browser_type="chrome")
            self.after(0, lambda: self.status_label.configure(text="Status: Logging in (Native Mode)...", text_color="blue"))
            
            # Wait for user to close the browser
            if self.bot.wait_for_native_login():
                Logger.info("Login process completed. Ready to start headless bot.")
                self.after(0, lambda: self.status_label.configure(text="Status: Login Saved. Ready to Start.", text_color="green"))
                self.after(0, lambda: self.start_btn.configure(state="normal"))
                self.after(0, lambda: self.stop_btn.configure(state="normal"))
            else:
                self.after(0, lambda: self.status_label.configure(text="Status: Login Cancelled", text_color="red"))
                self.after(0, lambda: self.launch_btn.configure(state="normal"))

        except Exception as e:
            Logger.error(f"Login process failed: {e}")
            self.after(0, lambda: self.launch_btn.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text="Status: Error", text_color="red"))

    def on_start_click(self):
        url = self.url_entry.get()
        if not url:
            Logger.error("Target URL is missing!")
            return
            
        self.start_btn.configure(state="disabled")
        self.status_label.configure(text="Status: Running (Headless)", text_color="green")
        
        threading.Thread(target=self._run_headless_task, args=(url,), daemon=True).start()

    def _run_headless_task(self, url):
        try:
            # Launch headless browser for the actual loop
            self.bot.launch_browser(headless=True)
            self.bot.start_loop(url)
        except Exception as e:
            Logger.error(f"Headless loop failed: {e}")
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text="Status: Error", text_color="red"))

    def on_stop_click(self):
        if self.bot:
            self.bot.stop_session()
        self.status_label.configure(text="Status: Stopped", text_color="gray")
        self.launch_btn.configure(state="normal")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
