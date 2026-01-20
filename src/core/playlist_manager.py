import json
import os
from src.utils.logger import Logger

class PlaylistStateManager:
    """Manages the state of playlist sequential playback."""
    
    def __init__(self, state_file="playlist_state.json"):
        self.state_file = state_file
        self.tracks = []
        self.current_index = 0
        self.is_loop_enabled = True
    
    def set_tracks(self, tracks):
        """Set the playlist tracks and reset index."""
        self.tracks = tracks
        self.current_index = 0
        Logger.info(f"Playlist loaded with {len(tracks)} tracks")
    
    def get_current_track(self):
        """Get the current track URL and info."""
        if not self.tracks or self.current_index >= len(self.tracks):
            return None
        return self.tracks[self.current_index]
    
    def advance_to_next(self):
        """Move to the next track, looping back to start if needed."""
        if not self.tracks:
            return None
        
        self.current_index += 1
        if self.current_index >= len(self.tracks):
            if self.is_loop_enabled:
                self.current_index = 0
                Logger.info("Looping back to first track in playlist")
            else:
                Logger.info("Reached end of playlist, no loop enabled")
                return None
        
        return self.get_current_track()
    
    def save_state(self):
        """Save current playlist state to file."""
        try:
            state = {
                "tracks": self.tracks,
                "current_index": self.current_index,
                "is_loop_enabled": self.is_loop_enabled
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            Logger.debug(f"Playlist state saved")
        except Exception as e:
            Logger.error(f"Failed to save playlist state: {e}")
    
    def load_state(self):
        """Load playlist state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.tracks = state.get("tracks", [])
                    self.current_index = state.get("current_index", 0)
                    self.is_loop_enabled = state.get("is_loop_enabled", True)
                Logger.info(f"Playlist state loaded: {len(self.tracks)} tracks, index {self.current_index}")
                return True
        except Exception as e:
            Logger.warning(f"Could not load playlist state: {e}")
        return False
    
    def clear_state(self):
        """Clear the playlist state."""
        self.tracks = []
        self.current_index = 0
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
