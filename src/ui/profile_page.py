import customtkinter as ctk
from src.utils.logger import Logger

class ProfilePage(ctk.CTkFrame):
    """Profile and statistics page UI."""
    
    def __init__(self, parent, stats_manager, on_logout_callback=None, on_back=None):
        super().__init__(parent, fg_color="#121212")
        
        self.stats_manager = stats_manager
        # Handle cases where callbacks might be missing or passed with different names
        self.on_logout_callback = on_logout_callback
        self.on_back_callback = on_back
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the profile page UI."""
        # Header with back button
        header_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back",
            width=100,
            height=40,
            fg_color="#282828",
            hover_color="#3e3e3e",
            command=self.on_back_callback,
            font=("Segoe UI", 14, "bold")
        )
        back_btn.pack(side="left", padx=15, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Profile & Statistics",
            font=("Segoe UI", 22, "bold"),
            text_color="#FFFFFF"
        )
        title_label.pack(side="left", padx=20)
        
        # Main content area with scrolling
        content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#121212",
            scrollbar_button_color="#535353",
            scrollbar_button_hover_color="#7a7a7a"
        )
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Listening Statistics Section
        stats_header = ctk.CTkLabel(
            content_frame,
            text="📊 Listening Statistics",
            font=("Segoe UI", 18, "bold"),
            text_color="#1DB954",
            anchor="w"
        )
        stats_header.pack(fill="x", pady=(10, 15))
        
        # Get current stats
        all_stats = self.stats_manager.get_all_stats()
        
        # Total listening time card
        time_card = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", corner_radius=12)
        time_card.pack(fill="x", pady=(0, 15))
        
        time_label = ctk.CTkLabel(
            time_card,
            text="Total Listening Time",
            font=("Segoe UI", 14),
            text_color="#b3b3b3",
            anchor="w"
        )
        time_label.pack(fill="x", padx=20, pady=(15, 5))
        
        time_value = ctk.CTkLabel(
            time_card,
            text=all_stats["total_time"],
            font=("Segoe UI", 32, "bold"),
            text_color="#1DB954",
            anchor="w"
        )
        time_value.pack(fill="x", padx=20, pady=(0, 15))
        
        # Song count card
        song_count_card = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", corner_radius=12)
        song_count_card.pack(fill="x", pady=(0, 20))
        
        count_label = ctk.CTkLabel(
            song_count_card,
            text="Unique Songs Played",
            font=("Segoe UI", 14),
            text_color="#b3b3b3",
            anchor="w"
        )
        count_label.pack(fill="x", padx=20, pady=(15, 5))
        
        count_value = ctk.CTkLabel(
            song_count_card,
            text=str(all_stats["song_count"]),
            font=("Segoe UI", 32, "bold"),
            text_color="#1DB954",
            anchor="w"
        )
        count_value.pack(fill="x", padx=20, pady=(0, 15))
        
        # Top Songs Section
        top_songs_header = ctk.CTkLabel(
            content_frame,
            text="🎵 Top Songs",
            font=("Segoe UI", 18, "bold"),
            text_color="#1DB954",
            anchor="w"
        )
        top_songs_header.pack(fill="x", pady=(20, 15))
        
        # Top songs table
        if all_stats["top_songs"]:
            for i, song in enumerate(all_stats["top_songs"], 1):
                song_frame = ctk.CTkFrame(content_frame, fg_color="#1a1a1a", corner_radius=8)
                song_frame.pack(fill="x", pady=5)
                
                # Rank badge
                rank_label = ctk.CTkLabel(
                    song_frame,
                    text=f"#{i}",
                    font=("Segoe UI", 14, "bold"),
                    text_color="#1DB954" if i <= 3 else "#b3b3b3",
                    width=40
                )
                rank_label.pack(side="left", padx=(15, 10), pady=12)
                
                # Song info container
                info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, pady=12)
                
                # Song name
                name_label = ctk.CTkLabel(
                    info_frame,
                    text=song["name"][:50] + ("..." if len(song["name"]) > 50 else ""),
                    font=("Segoe UI", 13, "bold"),
                    text_color="#FFFFFF",
                    anchor="w"
                )
                name_label.pack(fill="x")
                
                # Artist
                artist_label = ctk.CTkLabel(
                    info_frame,
                    text=song["artist"],
                    font=("Segoe UI", 11),
                    text_color="#b3b3b3",
                    anchor="w"
                )
                artist_label.pack(fill="x")
                
                # Play count and time
                stats_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
                stats_frame.pack(side="right", padx=15, pady=12)
                
                plays_label = ctk.CTkLabel(
                    stats_frame,
                    text=f"{song['play_count']} plays",
                    font=("Segoe UI", 12, "bold"),
                    text_color="#1DB954"
                )
                plays_label.pack(anchor="e")
                
                time_label = ctk.CTkLabel(
                    stats_frame,
                    text=song["total_time"],
                    font=("Segoe UI", 11),
                    text_color="#b3b3b3"
                )
                time_label.pack(anchor="e")
        else:
            no_data_label = ctk.CTkLabel(
                content_frame,
                text="No listening data yet. Start playing some music!",
                font=("Segoe UI", 13),
                text_color="#b3b3b3"
            )
            no_data_label.pack(pady=20)
        
        # Bottom actions - Just Refresh Button
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        # Refresh button - Centered and consistent width
        refresh_btn = ctk.CTkButton(
            actions_frame,
            text="🔄 Refresh Statistics",
            width=250,
            height=45,
            fg_color="#1DB954",
            hover_color="#1ed760",
            command=self.refresh_stats,
            font=("Segoe UI", 14, "bold"),
            corner_radius=22
        )
        refresh_btn.pack(pady=15)
    
    def refresh_stats(self):
        """Refresh the statistics display."""
        Logger.info("Refreshing profile statistics...")
        # Rebuild the entire UI to show updated stats
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()
