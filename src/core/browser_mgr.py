import shutil
import os
import logging
import platform
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import undetected_chromedriver as uc

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
    def ensure_browser_installed():
        """Checks if a browser is available, if not, installs playwright chromium."""
        chrome = BrowserManager.get_chrome_path()
        firefox = BrowserManager.get_firefox_path()
        
        if not chrome and not firefox:
            logging.info("No system browser found. Attempting to install Playwright Chromium...")
            try:
                import sys
                subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                logging.info("Playwright Chromium installed successfully.")
                return True
            except Exception as e:
                logging.error(f"Failed to install Playwright browser: {e}")
                return False
        return True

    @staticmethod
    def find_portable_browser(browser_type="chromium"):
        """
        Looks for browsers installed by Playwright in standard locations.
        """
        home = os.path.expanduser("~")
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            base_path = os.path.join(os.getenv("LOCALAPPDATA", ""), "ms-playwright")
        else:
            base_path = os.path.join(home, ".cache", "ms-playwright")
        
        if not os.path.exists(base_path):
            return None
            
        for folder in os.listdir(base_path):
            if folder.startswith(browser_type):
                if browser_type == "chromium":
                    if is_windows:
                        chrome_bin = os.path.join(base_path, folder, "chrome-win64", "chrome.exe")
                        if not os.path.exists(chrome_bin):
                             chrome_bin = os.path.join(base_path, folder, "chrome-win", "chrome.exe")
                    else:
                        chrome_bin = os.path.join(base_path, folder, "chrome-linux64", "chrome")
                        
                    if os.path.exists(chrome_bin):
                        return chrome_bin
                elif browser_type == "firefox":
                    if is_windows:
                        firefox_bin = os.path.join(base_path, folder, "firefox", "firefox.exe")
                    else:
                        firefox_bin = os.path.join(base_path, folder, "firefox", "firefox")
                        
                    if os.path.exists(firefox_bin):
                        return firefox_bin
        return None

    @staticmethod
    def get_chrome_path():
        """Returns the detected path to Chrome/Chromium."""
        is_windows = platform.system() == "Windows"
        path = shutil.which("google-chrome") or \
               shutil.which("google-chrome-stable") or \
               shutil.which("chromium") or \
               shutil.which("chromium-browser") or \
               shutil.which("chrome")
        if path: return path
        
        if is_windows:
            win_paths = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("LocalAppData", ""), "Google\\Chrome\\Application\\chrome.exe")
            ]
            for p in win_paths:
                if os.path.exists(p): return p
                
        return BrowserManager.find_portable_browser("chromium")

    @staticmethod
    def get_firefox_path():
        """Returns the detected path to Firefox."""
        is_windows = platform.system() == "Windows"
        path = shutil.which("firefox")
        if path: return path
        
        if is_windows:
            win_paths = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Mozilla Firefox\\firefox.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Mozilla Firefox\\firefox.exe")
            ]
            for p in win_paths:
                if os.path.exists(p): return p
                
        return BrowserManager.find_portable_browser("firefox")

    @staticmethod
    def launch_controlled_login(user_data_dir="spotify_profile"):
        """
        Launches a Playwright-controlled browser for login.
        Monitors the URL and closes automatically when success is detected.
        """
        from playwright.sync_api import sync_playwright
        
        abs_profile_path = os.path.abspath(user_data_dir)
        BrowserManager._cleanup_locks(abs_profile_path)

        def run(playwright):
            chrome_path = BrowserManager.get_chrome_path()
            
            launch_args = {
                "user_data_dir": abs_profile_path,
                "headless": False,
                "args": ["--no-first-run", "--no-default-browser-check"]
            }
            if chrome_path:
                launch_args["executable_path"] = chrome_path

            context = None
            try:
                context = playwright.chromium.launch_persistent_context(**launch_args)
                page = context.new_page()
                page.goto("https://accounts.spotify.com/en/login")
                
                logging.info("Controlled login window opened. Waiting for login detection...")
                
                start_time = time.time()
                timeout = 600 # 10 minutes
                
                while time.time() - start_time < timeout:
                    try:
                        # 1. Check if browser/page is still alive
                        if page.is_closed():
                            logging.info("Browser window closed. Assuming user is done/logged in.")
                            return True, None
                        
                        url = page.url.lower()
                        
                        # A. Instant URL Detection (Aggressive)
                        # If we are on a status or account page, it's a 100% success.
                        if "/status" in url or "/account/overview" in url or "open.spotify.com" in url:
                            # Final safety: make sure we aren't just starting the login flow
                            if not url.endswith("/login") and "auth" not in url:
                                logging.info(f"Login SUCCESS detected via URL: {url}")
                                
                                # --- PROFILE DATA EXTRACTION ---
                                profile_data = {"name": "Spotify User", "avatar": None}
                                try:
                                    # Wait a bit for elements to load
                                    page.wait_for_selector("[data-testid='user-widget-link'], h3, .username, p", timeout=5000)
                                    
                                    profile_data = page.evaluate("""() => {
                                        const profile = { name: "Spotify User", avatar: null };
                                        
                                        // 1. Metadata Extraction (The most reliable, language-agnostic source)
                                        // Found on account and status pages.
                                        try {
                                            const bootstrapMeta = document.querySelector('meta#bootstrap-data');
                                            if (bootstrapMeta) {
                                                const data = JSON.parse(bootstrapMeta.getAttribute('sp-bootstrap-data'));
                                                if (data && data.user && data.user.displayName) {
                                                    profile.name = data.user.displayName.trim();
                                                }
                                            }
                                        } catch (e) {}

                                        if (profile.name === "Spotify User") {
                                            // 2. Web Player / Modern Widget
                                            const widget = document.querySelector('[data-testid="user-widget-link"]');
                                            if (widget) {
                                                const span = widget.querySelector('span');
                                                if (span && span.innerText.trim()) {
                                                    profile.name = span.innerText.trim();
                                                } else {
                                                    profile.name = widget.innerText.trim();
                                                }
                                            }
                                        }

                                        // 3. Account Page Fallback 
                                        if (profile.name === "Spotify User") {
                                            const structuralTargets = [
                                                document.querySelector('[data-testid="profile-card-name"]'),
                                                document.querySelector('h1[data-testid="display-name"]'),
                                                document.querySelector('div[class*="sc-"]'),
                                                document.querySelector('.profile-name')
                                            ];
                                            
                                            for (let el of structuralTargets) {
                                                if (el && el.innerText.trim() && el.innerText.length < 40) {
                                                    profile.name = el.innerText.trim();
                                                    break;
                                                }
                                            }
                                        }

                                        // Avatar Detection
                                        const img = document.querySelector('img[data-testid="user-widget-avatar"], .profile-image img, img[alt*="profile"]');
                                        if (img) profile.avatar = img.src;
                                        
                                        return profile;
                                    }""")
                                except: pass
                                # -------------------------------
                                # -------------------------------
                                # -------------------------------
                                # -------------------------------

                                time.sleep(2)
                                try: context.close()
                                except: pass
                                return True, profile_data

                        # B. DOM-Based Detection (Multilingual Backup)
                        try:
                            is_logged_in = page.evaluate("""() => {
                                const text = document.body.innerText.toLowerCase();
                                const indicators = ['abmelden', 'logout', 'log out', 'oturumu kapat', 'angemeldet als', 'logged in as'];
                                return indicators.some(ind => text.includes(ind)) || 
                                       !!document.querySelector('[data-testid="user-widget-link"]') ||
                                       !!document.querySelector('button[aria-label="Profile"]');
                            }""")
                            
                            if is_logged_in:
                                if "login" not in url and "signup" not in url:
                                    logging.info("Login SUCCESS detected via Page Content.")
                                    
                                    # --- PROFILE DATA EXTRACTION ---
                                    profile_data = {"name": "Spotify User", "avatar": None}
                                    try:
                                        page.wait_for_selector("[data-testid='user-widget-link'], h3, .username, p", timeout=3000)
                                        profile_data = page.evaluate("""() => {
                                            const profile = { name: "Spotify User", avatar: null };
                                            
                                            // 1. Web Player / Modern Widget
                                            const widget = document.querySelector('[data-testid="user-widget-link"]');
                                            if (widget) {
                                                const span = widget.querySelector('span');
                                                profile.name = span ? span.innerText.trim() : (widget.getAttribute('aria-label') || widget.innerText.trim());
                                            }

                                            // 2. Account Page Fallbacks
                                            if (profile.name === "Spotify User") {
                                                const structuralTargets = [
                                                    document.querySelector('[data-testid="profile-card-name"]'),
                                                    document.querySelector('h1'),
                                                    document.querySelector('div[class*="sc-"]')
                                                ];
                                                for (let el of structuralTargets) {
                                                    if (el && el.innerText.trim() && el.innerText.length < 30) {
                                                        profile.name = el.innerText.trim();
                                                        break;
                                                    }
                                                }
                                            }

                                            // 3. Avatar
                                            const img = document.querySelector('img[data-testid="user-widget-avatar"]');
                                            if (img) profile.avatar = img.src;
                                            
                                            return profile;
                                        }""")
                                    except: pass
                                    # -------------------------------

                                    time.sleep(2)
                                    try: context.close()
                                    except: pass
                                    return True, profile_data
                        except: pass

                        time.sleep(0.5) # Faster polling
                    except Exception as e:
                        # Catch EPIPE, "Target closed", etc.
                        err_str = str(e).lower()
                        if any(x in err_str for x in ["broken pipe", "connection closed", "target closed"]):
                            logging.info("Browser connection lost/closed. Proceeding...")
                            return True, None
                        break
            except Exception as e:
                logging.error(f"Controlled login main loop failed: {e}")
                return True, None # Fallback: let the user try to proceed
            finally:
                if context:
                    try: context.close()
                    except: pass
            
            return False, None

        try:
            with sync_playwright() as playwright:
                return run(playwright)
        except Exception as e:
            logging.error(f"Playwright Sync Error: {e}")
            return True, None # Fallback

    @staticmethod
    def launch(headless=False, user_data_dir="spotify_profile"):
        """
        Launches a browser with a persistent profile.
        """
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        abs_profile_path = os.path.abspath(user_data_dir)
        if not os.path.exists(abs_profile_path):
            os.makedirs(abs_profile_path)

        chrome_path = BrowserManager.get_chrome_path()
        if chrome_path:
            options = uc.ChromeOptions()
            if headless: options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--mute-audio')
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument(f'--user-data-dir={abs_profile_path}')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--force-device-scale-factor=1')
            options.add_argument('--disable-infobars')
            options.add_argument('--hide-scrollbars')
            
            BrowserManager._cleanup_locks(abs_profile_path)
            try:
                driver = uc.Chrome(options=options, browser_executable_path=chrome_path, headless=headless, use_subprocess=True, version_main=None)
                driver.set_window_size(1920, 1080)
                return driver
            except Exception as e:
                logging.warning(f"Chrome UC launch failed: {e}. Trying Firefox...")

        firefox_path = BrowserManager.get_firefox_path()
        if firefox_path:
            options = webdriver.FirefoxOptions()
            if headless: options.add_argument('--headless')
            options.binary_location = firefox_path
            options.set_preference("general.useragent.override", user_agent)
            options.add_argument("-profile")
            options.add_argument(abs_profile_path)
            try:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
                driver.set_window_size(1920, 1080)
                return driver
            except Exception as e:
                logging.error(f"Firefox launch failed: {e}")

        raise FileNotFoundError("Could not find any browser.")
