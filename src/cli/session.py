"""Session management for CLI"""
import os
from src.core.browser_mgr import BrowserManager

class CLISession:
    """Manages CLI session state and authentication"""
    
    @staticmethod
    def is_logged_in():
        """
        Check if user is authenticated (cookies exist).
        
        Returns:
            bool: True if cookies exist
        """
        return BrowserManager.has_cookies()
    
    @staticmethod
    def require_login():
        """
        Ensure user is logged in before proceeding.
        Exits with error if not authenticated.
        """
        if not CLISession.is_logged_in():
            print("[X] Not authenticated. Please run: python cli.py login")
            exit(1)
    
    @staticmethod
    def clear_session():
        """Clear session cookies"""
        try:
            cookie_file = os.path.join("spotify_profile", "cookies.json")
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
                return True
            return False
        except Exception as e:
            print(f"Warning: Could not delete cookies: {e}")
            return False
