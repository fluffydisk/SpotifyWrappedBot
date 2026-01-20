import logging
import os
from datetime import datetime

class Logger:
    """
    Centralized logging utility with GUI support and advanced debugging.
    """
    _callbacks = []
    _screenshot_dir = "screenshots"
    _logger = None

    @staticmethod
    def init():
        # Ensure screenshot directory exists
        if not os.path.exists(Logger._screenshot_dir):
            os.makedirs(Logger._screenshot_dir)

        # Standard Logger setup
        logger = logging.getLogger("SpotifyBot")
        logger.setLevel(logging.DEBUG)
        
        # Prevent adding handlers multiple times
        if not logger.handlers:
            # File Handler for standard INFO logs
            file_handler = logging.FileHandler("bot.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # File Handler for VERBOSE DEBUG logs
            debug_handler = logging.FileHandler("bot_debug.log")
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
            
            # Stream Handler (Console)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

            logger.addHandler(file_handler)
            logger.addHandler(debug_handler)
            logger.addHandler(stream_handler)
        
        Logger._logger = logger

    @staticmethod
    def add_callback(callback):
        """Adds a callback function to receive log messages."""
        if callback not in Logger._callbacks:
            Logger._callbacks.append(callback)

    @staticmethod
    def _log(level, msg):
        """Internal log handler that dispatches to logging and callbacks."""
        if Logger._logger:
            if level == "INFO":
                Logger._logger.info(msg)
            elif level == "ERROR":
                Logger._logger.error(msg)
            elif level == "WARNING":
                Logger._logger.warning(msg)
            elif level == "DEBUG":
                Logger._logger.debug(msg)
        else:
            # Fallback if init not called
            print(f"[{level}] {msg}")

        # Dispatch to GUI callbacks (Only INFO, WARNING and ERROR to avoid flooding GUI)
        if level in ["INFO", "WARNING", "ERROR"]:
            formatted_msg = f"[{level}] {msg}"
            for callback in Logger._callbacks:
                try:
                    callback(formatted_msg)
                except Exception:
                    pass

    @staticmethod
    def info(msg):
        Logger._log("INFO", msg)

    @staticmethod
    def error(msg):
        Logger._log("ERROR", msg)

    @staticmethod
    def warning(msg):
        Logger._log("WARNING", msg)

    @staticmethod
    def debug(msg):
        Logger._log("DEBUG", msg)

    @staticmethod
    def capture_screenshot(browser, name_prefix="error"):
        """
        Captures a screenshot for debugging purposes.
        Also checks and enforces Spotify UI mute status.
        """
        # First, check and ensure Spotify is muted
        volume_status = "Unknown"
        try:
            from selenium.webdriver.common.by import By
            selector = "button[data-testid='control-button-mute']"
            btn_elements = browser.find_elements(By.CSS_SELECTOR, selector)
            
            if btn_elements:
                btn = btn_elements[0]
                label = btn.get_attribute("aria-label") or ""
                
                # Check if currently muted
                muted_labels = ["unmute", "sesi aç", "stummschaltung aufheben"]
                is_muted = any(target in label.lower() for target in muted_labels)
                
                if is_muted:
                    volume_status = "✓ MUTED"
                    Logger.debug("Volume check: Spotify UI is MUTED ✓")
                else:
                    volume_status = "⚠ NOT MUTED - Auto-muting"
                    Logger.warning("Volume check: Spotify UI was NOT muted! Fixing...")
                    browser.execute_script("arguments[0].click();", btn)
                    Logger.info("Spotify UI re-muted for safety")
            else:
                volume_status = "No volume control found"
        except Exception as e:
            volume_status = f"Error checking: {e}"
            Logger.debug(f"Volume check failed: {e}")
        
        # Capture screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Logger._screenshot_dir}/{name_prefix}_{timestamp}.png"
        try:
            browser.save_screenshot(filename)
            Logger.info(f"Screenshot saved: {filename} | Volume: {volume_status}")
        except Exception as e:
            Logger.error(f"Failed to capture screenshot: {e}")
