import shutil
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import subprocess

class BrowserManager:
    """
    Manages browser instances with support for Chrome (UC) and Firefox.
    Focuses on persistence via User Data Directories and portability via Playwright binaries.
    """
    @staticmethod
    def _cleanup_locks(profile_path):
        """Removes stale Chrome lock files to prevent 'SingletonLock' errors."""
        for lock_name in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lock_path = os.path.join(profile_path, lock_name)
            if os.path.exists(lock_path):
                try:
                    if os.path.islink(lock_path):
                        os.unlink(lock_path)
                    else:
                        os.remove(lock_path)
                except:
                    pass

    @staticmethod
    def find_portable_browser(browser_type="chromium"):
        """
        Looks for browsers installed by Playwright in standard locations.
        """
        home = os.path.expanduser("~")
        base_path = os.path.join(home, ".cache", "ms-playwright")
        
        if not os.path.exists(base_path):
            return None
            
        # Search for chromium or firefox folders
        for folder in os.listdir(base_path):
            if folder.startswith(browser_type):
                # Traverse to binary
                if browser_type == "chromium":
                    # chromium-XXXX/chrome-linux/chrome
                    chrome_bin = os.path.join(base_path, folder, "chrome-linux64", "chrome")
                    if os.path.exists(chrome_bin):
                        return chrome_bin
                elif browser_type == "firefox":
                    # firefox-XXXX/firefox/firefox
                    firefox_bin = os.path.join(base_path, folder, "firefox", "firefox")
                    if os.path.exists(firefox_bin):
                        return firefox_bin
        return None

    @staticmethod
    def launch_native(browser_type="chrome", user_data_dir="spotify_profile"):
        """
        Launches the browser as a standard system process (not Selenium controlled).
        This bypasses ALL automation detection, useful for Google/Spotify logins.
        """
        abs_profile_path = os.path.abspath(user_data_dir)
        if not os.path.exists(abs_profile_path):
            os.makedirs(abs_profile_path)
        else:
            BrowserManager._cleanup_locks(abs_profile_path)
            
        if browser_type == "chrome":
            chrome_path = shutil.which("google-chrome") or \
                          shutil.which("google-chrome-stable") or \
                          shutil.which("chrome") or \
                          BrowserManager.find_portable_browser("chromium")
            if chrome_path:
                cmd = [
                    chrome_path,
                    f"--user-data-dir={abs_profile_path}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "https://accounts.spotify.com/en/login"
                ]
                return subprocess.Popen(cmd)
        
        elif browser_type == "firefox":
            firefox_path = shutil.which("firefox") or BrowserManager.find_portable_browser("firefox")
            if firefox_path:
                cmd = [
                    firefox_path,
                    "-profile", abs_profile_path,
                    "-new-tab", "https://accounts.spotify.com/en/login"
                ]
                return subprocess.Popen(cmd)
        
        return None

    @staticmethod
    def launch(headless=False, user_data_dir="spotify_profile"):
        """
        Launches a browser with a persistent profile.
        Preference: Global Chrome > Playwright Chromium (UC) > Global Firefox > Playwright Firefox.
        """
        # Use a fixed Desktop User-Agent to avoid mobile app redirects
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Ensure absolute path for profile
        abs_profile_path = os.path.abspath(user_data_dir)
        if not os.path.exists(abs_profile_path):
            os.makedirs(abs_profile_path)
            logging.info(f"Created new profile directory: {abs_profile_path}")

        # 1. Try Chrome/Chromium (Global or Portable) with Undetected Chromedriver
        chrome_path = shutil.which("google-chrome") or \
                      shutil.which("google-chrome-stable") or \
                      shutil.which("chromium") or \
                      shutil.which("chromium-browser") or \
                      shutil.which("chrome") or \
                      BrowserManager.find_portable_browser("chromium")
        
        if chrome_path:
            logging.info(f"Chrome/Chromium path: {chrome_path}. Launching with profile: {abs_profile_path}")
            options = uc.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--mute-audio')
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument(f'--user-data-dir={abs_profile_path}')
            
            # Additional flags for stability in headless mode
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--force-device-scale-factor=1')
            options.add_argument('--disable-infobars')
            options.add_argument('--hide-scrollbars')
            
            # Cleanup potential lock files from previous crashes
            BrowserManager._cleanup_locks(abs_profile_path)

            try:
                # Basic options for stability
                driver = uc.Chrome(
                    options=options,
                    browser_executable_path=chrome_path,
                    headless=headless,
                    use_subprocess=True,
                    version_main=None # Auto-detect version
                )
                driver.set_window_size(1920, 1080)
                return driver
            except Exception as e:
                logging.warning(f"Chrome UC launch failed: {e}. Trying Firefox...")

        # 2. Try Firefox (Global or Portable) as fallback
        firefox_path = shutil.which("firefox") or BrowserManager.find_portable_browser("firefox")
        if firefox_path:
            logging.info(f"Firefox path: {firefox_path}. Launching with profile: {abs_profile_path}")
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            options.binary_location = firefox_path
            options.set_preference("general.useragent.override", user_agent)
            
            # Firefox profile path setting
            options.add_argument("-profile")
            options.add_argument(abs_profile_path)
            options.add_argument('--width=1920')
            options.add_argument('--height=1080')
            
            try:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
                driver.set_window_size(1920, 1080)
                return driver
            except Exception as e:
                logging.error(f"Firefox launch failed: {e}")

        raise FileNotFoundError("Could not find any browser (Chrome/Chromium/Firefox), even after attempting portable download.")
