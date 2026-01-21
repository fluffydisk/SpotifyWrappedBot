import customtkinter as ctk
import json

# Color Palette (matching main window)
COLORS = {
    "bg_dark": "#0D0D0D",
    "bg_card": "#1A1A1A",
    "bg_input": "#252525",
    "accent_primary": "#1DB954",
    "accent_secondary": "#1ED760",
    "danger": "#E63946",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B3B3B3",
    "text_muted": "#6B6B6B",
    "border": "#333333",
}

class CookieDialog(ctk.CTkToplevel):
    """
    Dialog window for importing Spotify cookies.
    Simple 2-field interface for sp_dc and sp_key.
    """
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        
        self.on_success = on_success
        
        # Window configuration
        self.title("Import Spotify Session")
        self.geometry("650x750")  # Optimized size
        self.configure(fg_color=COLORS["bg_dark"])
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Header
        header_label = ctk.CTkLabel(
            main_frame,
            text="🔐 Import Spotify Session",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        header_label.pack(pady=(0, 8))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Connect your Spotify account by importing cookies",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Instructions Frame - Detailed steps
        instructions_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        instructions_frame.pack(fill="x", pady=(0, 20))
        
        instructions_inner = ctk.CTkFrame(instructions_frame, fg_color="transparent")
        instructions_inner.pack(fill="x", padx=20, pady=20)
        
        # Detailed step-by-step instructions
        steps = [
            ("1️⃣", "Open Spotify Web Player", "https://open.spotify.com"),
            ("2️⃣", "Sign in with your account", "Google, Facebook, Apple, or Email"),
            ("3️⃣", "Press F12 → Application → Cookies", "Navigate to cookie storage"),
            ("4️⃣", "Copy sp_dc and sp_key values", "Find these two cookies and paste below")
        ]
        
        for emoji, main_text, sub_text in steps:
            step_frame = ctk.CTkFrame(instructions_inner, fg_color="transparent")
            step_frame.pack(fill="x", pady=5)
            
            # Emoji
            emoji_label = ctk.CTkLabel(
                step_frame,
                text=emoji,
                font=ctk.CTkFont(size=16),
                width=35
            )
            emoji_label.pack(side="left", padx=(0, 12))
            
            # Text container
            text_frame = ctk.CTkFrame(step_frame, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            
            # Main instruction
            main_label = ctk.CTkLabel(
                text_frame,
                text=main_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS["text_primary"],
                anchor="w"
            )
            main_label.pack(fill="x")
            
            # Sub-instruction
            if sub_text:
                sub_label = ctk.CTkLabel(
                    text_frame,
                    text=f"→ {sub_text}",
                    font=ctk.CTkFont(size=11),
                    text_color=COLORS["text_muted"],
                    anchor="w"
                )
                sub_label.pack(fill="x")
        
        # sp_dc input
        sp_dc_label = ctk.CTkLabel(
            main_frame,
            text="Cookie: sp_dc",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        sp_dc_label.pack(fill="x", pady=(0, 6))
        
        self.sp_dc_input = ctk.CTkEntry(
            main_frame,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_input"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text="Paste sp_dc value here..."
        )
        self.sp_dc_input.pack(fill="x", pady=(0, 15))
        
        # sp_key input
        sp_key_label = ctk.CTkLabel(
            main_frame,
            text="Cookie: sp_key",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        sp_key_label.pack(fill="x", pady=(0, 6))
        
        self.sp_key_input = ctk.CTkEntry(
            main_frame,
            height=45,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLORS["bg_input"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            placeholder_text="Paste sp_key value here..."
        )
        self.sp_key_input.pack(fill="x", pady=(0, 15))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(pady=(0, 15))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            command=self.destroy
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
        # Import button
        import_btn = ctk.CTkButton(
            button_frame,
            text="→ Import & Sign In",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=COLORS["accent_primary"],
            hover_color=COLORS["accent_secondary"],
            text_color=COLORS["text_primary"],
            command=self._import_cookies
        )
        import_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")
    
    def _import_cookies(self):
        """Validate and import cookies"""
        sp_dc = self.sp_dc_input.get().strip()
        sp_key = self.sp_key_input.get().strip()
        
        # Validate
        if not sp_dc:
            self._set_status("❌ Please enter sp_dc cookie value", COLORS["danger"])
            return
        
        if not sp_key:
            self._set_status("❌ Please enter sp_key cookie value", COLORS["danger"])
            return
        
        # Basic validation - check if values look reasonable
        if len(sp_dc) < 10:
            self._set_status("❌ sp_dc value seems too short", COLORS["danger"])
            return
        
        if len(sp_key) < 5:
            self._set_status("❌ sp_key value seems too short", COLORS["danger"])
            return
        
        # Convert to JSON format
        cookies = [
            {
                "name": "sp_dc",
                "value": sp_dc,
                "domain": ".spotify.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            },
            {
                "name": "sp_key",
                "value": sp_key,
                "domain": ".spotify.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            }
        ]
        
        # Call success callback
        if self.on_success:
            self.on_success(cookies)
        
        # Close dialog
        self.destroy()
    
    def _set_status(self, text, color):
        """Update status label"""
        self.status_label.configure(text=text, text_color=color)
