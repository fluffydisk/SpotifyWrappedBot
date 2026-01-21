import json
import os
from datetime import datetime
from src.utils.logger import Logger

class StatisticsManager:
    """Manages listening statistics based on verified Spotify playback."""
    
    def __init__(self, stats_file="listening_stats.json"):
        self.stats_file = stats_file
        self.data = {
            "total_listening_seconds": 0,
            "songs": {},
            "last_updated": None
        }
        self.load()
    
    def increment_play(self, track_url, title="Unknown", artist="Unknown"):
        """Increment play count for a song after verified playback cycle."""
        track_id = self._extract_track_id(track_url)
        
        if track_id not in self.data["songs"]:
            self.data["songs"][track_id] = {
                "name": title,
                "artist": artist,
                "play_count": 0,
                "total_time_seconds": 0,
                "url": track_url
            }
        
        self.data["songs"][track_id]["play_count"] += 1
        self.data["last_updated"] = datetime.now().isoformat()
        
        Logger.info(f"Stats: {title} play count → {self.data['songs'][track_id]['play_count']}")
        self.save()
    
    def add_listening_time(self, track_url, duration_seconds):
        """Add listening time for a song (called after verified playback)."""
        track_id = self._extract_track_id(track_url)
        
        if track_id in self.data["songs"]:
            self.data["songs"][track_id]["total_time_seconds"] += duration_seconds
            self.data["total_listening_seconds"] += duration_seconds
            self.data["last_updated"] = datetime.now().isoformat()
            
            Logger.debug(f"Stats: Added {duration_seconds}s to {self.data['songs'][track_id]['name']}")
            self.save()
    
    def get_total_time_formatted(self):
        """Get total listening time as formatted string."""
        total = self.data["total_listening_seconds"]
        hours = total // 3600
        minutes = (total % 3600) // 60
        
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_top_songs(self, limit=10):
        """Get top songs by play count."""
        songs_list = []
        for track_id, data in self.data["songs"].items():
            songs_list.append({
                "name": data["name"],
                "artist": data["artist"],
                "play_count": data["play_count"],
                "total_time": self._format_duration(data["total_time_seconds"])
            })
        
        # Sort by play count descending
        songs_list.sort(key=lambda x: x["play_count"], reverse=True)
        return songs_list[:limit]
    
    def get_all_stats(self):
        """Get all statistics data."""
        return {
            "total_time": self.get_total_time_formatted(),
            "total_time_seconds": self.data["total_listening_seconds"],
            "song_count": len(self.data["songs"]),
            "top_songs": self.get_top_songs(),
            "last_updated": self.data["last_updated"]
        }
    
    def save(self):
        """Save statistics to file."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            Logger.debug(f"Statistics saved to {self.stats_file}")
        except Exception as e:
            Logger.error(f"Failed to save statistics: {e}")
    
    def load(self):
        """Load statistics from file."""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.data.update(loaded_data)
                Logger.info(f"Statistics loaded: {len(self.data['songs'])} songs, {self.get_total_time_formatted()} total")
        except Exception as e:
            Logger.warning(f"Could not load statistics: {e}")
    
    def clear_stats(self):
        """Clear all statistics."""
        self.data = {
            "total_listening_seconds": 0,
            "songs": {},
            "last_updated": None
        }
        self.save()
        Logger.info("Statistics cleared")
    
    def _extract_track_id(self, track_url):
        """Extract Spotify track ID from URL."""
        # Handle both full URLs and track IDs
        if "spotify.com/track/" in track_url:
            return track_url.split("/track/")[-1].split("?")[0]
        elif "spotify:track:" in track_url:
            return track_url.split("spotify:track:")[-1]
        else:
            return track_url  # Assume it's already an ID
    
    def _format_duration(self, seconds):
        """Format duration in seconds to readable string."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
