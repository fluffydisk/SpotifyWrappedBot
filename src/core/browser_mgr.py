import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class BrowserManager:
    """Manages Selenium browser instances with cookie-based authentication."""

    @staticmethod
    def save_cookies(cookies, profile_dir="spotify_profile"):
        """
        Saves cookies to JSON file for session persistence.
        
        Args:
            cookies: List of cookie dictionaries
            profile_dir: Directory to store cookies
            
        Returns:
            bool: True if successful
        """
        try:
            abs_profile = os.path.abspath(profile_dir)
            os.makedirs(abs_profile, exist_ok=True)
            
            filepath = os.path.join(abs_profile, "cookies.json")
            
            with open(filepath, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logging.info(f"Cookies saved to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Failed to save cookies: {e}")
            return False

    @staticmethod
    def load_cookies(driver,profile_dir="spotify_profile"):
        """
        Loads cookies from JSON file into browser session.
        
        Args:
            driver: Selenium WebDriver instance
            profile_dir: Directory containing cookies
            
        Returns:
            bool: True if cookies loaded successfully
        """
        try:
            abs_profile = os.path.abspath(profile_dir)
            filepath = os.path.join(abs_profile, "cookies.json")
            
            if not os.path.exists(filepath):
                logging.debug(f"Cookie file not found: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                cookies = json.load(f)
            
            # Must be on Spotify domain to add cookies
            driver.get("https://open.spotify.com/")
            
            for cookie in cookies:
                try:
                    # Add required fields if missing
                    if "domain" not in cookie:
                        cookie["domain"] = ".spotify.com"
                    if "path" not in cookie:
                        cookie["path"] = "/"
                    if "secure" not in cookie:
                        cookie["secure"] = True
                    if "httpOnly" not in cookie:
                        cookie["httpOnly"] = False
                    
                    # Remove problematic fields
                    cookie.pop("sameSite", None)
                    cookie.pop("expiry", None)
                    
                    driver.add_cookie(cookie)
                except Exception as e:
                    logging.debug(f"Failed to add cookie {cookie.get('name')}: {e}")
                    continue
            
            logging.info("Cookies loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to load cookies: {e}")
            return False

    @staticmethod
    def has_cookies(profile_dir="spotify_profile"):
        """
        Check if cookies exist in profile directory.
        
        Args:
            profile_dir: Directory to check
            
        Returns:
            bool: True if cookies file exists
        """
        abs_profile = os.path.abspath(profile_dir)
        filepath = os.path.join(abs_profile, "cookies.json")
        return os.path.exists(filepath)

    @staticmethod
    def launch(headless=False, user_data_dir="spotify_profile"):
        """
        Launches a Selenium Chrome instance.
        Automatically loads saved cookies if available.
        
        Args:
            headless: Run in headless mode
            user_data_dir: Profile directory (for cookie loading)
            
        Returns:
            WebDriver instance
        """
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        
        # CRITICAL: Mute all audio output
        options.add_argument("--mute-audio")
        options.add_argument("--disable-audio-output")
        
        # Performance & Stability
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--window-size=1280,800")
        
        # User Agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Suppress logs
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Stealth fix
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Load cookies if available
        if BrowserManager.has_cookies(user_data_dir):
            logging.info("Loading saved session cookies...")
            BrowserManager.load_cookies(driver, user_data_dir)
            # Refresh to apply cookies
            driver.refresh()
        
        return driver
