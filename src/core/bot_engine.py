import time
import random
import threading
from src.core.browser_mgr import BrowserManager
from src.utils.logger import Logger
from src.utils.humanizer import Humanizer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SpotifyBot:
    """
    Pure automation engine for Spotify. Controls DOM directly, manages loops,
    and watches for 'Still listening' popups.
    """
    def __init__(self, settings):
        self.settings = settings
        self.browser = None
        self.running = False
        self.watcher_thread = None

    def launch_native_login(self):
        """Launches a controlled browser for login and returns (success, profile_data)."""
        Logger.info(f"Starting controlled browser for login...")
        profile_dir = self.settings.get('profile_dir', 'spotify_profile')
        
        # This will block until login is detected or window is closed
        success, profile_data = BrowserManager.launch_controlled_login(profile_dir)
        
        if success:
            Logger.info("Login SUCCESS! Session saved.")
            return True, profile_data
        else:
            Logger.warning("Login was not completed or window was closed.")
            return False, None

    def wait_for_native_login(self):
        """Legacy method, logic now moved into launch_native_login."""
        return True

    def launch_browser(self, headless=False):
        """Launches the browser with user profile."""
        Logger.info(f"Starting browser session (Headless={headless})...")
        try:
            profile_dir = self.settings.get('profile_dir', 'spotify_profile')
            self.browser = BrowserManager.launch(
                headless=headless,
                user_data_dir=profile_dir
            )
            self.running = True
            
            # Navigate to Spotify
            if not headless:
                self.browser.get("https://accounts.spotify.com/en/login")
            else:
                self.browser.get("https://open.spotify.com/")
                
            # Start Background Watcher
            self.start_watcher()
            
        except Exception as e:
            Logger.error(f"Launch Error: {e}")
            raise e

    def wait_for_login(self, timeout=300):
        """
        Waits for the user to log in manually. 
        Detects success by checking the URL.
        """
        Logger.info("Waiting for manual login (timeout: 5 minutes)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.running: return False
            try:
                url = self.browser.current_url
                if "open.spotify.com" in url or ("accounts.spotify.com" not in url and "spotify.com" in url):
                    Logger.info("Login detected!")
                    return True
            except:
                pass
            time.sleep(2)
        Logger.error("Login timed out.")
        return False

    def start_watcher(self):
        """Starts a background thread to handle popups and interruptions."""
        if self.watcher_thread and self.watcher_thread.is_alive():
            return
            
        Logger.debug("Starting background watcher...")
        self.watcher_thread = threading.Thread(target=self._watcher_loop, daemon=True)
        self.watcher_thread.start()

    def _watcher_loop(self):
        """Periodically checks for 'Still listening', cookie banners, or login popups."""
        while self.running:
            try:
                if not self.browser: break
                
                # Check if browser is still responsive
                try: 
                    _ = self.browser.current_url
                except:
                    break
                
                # 1. Cookie Banners / Consent Popups
                cookie_selectors = [
                    "button#onetrust-accept-btn-handler",
                    "button[id='onetrust-accept-btn-handler']",
                    "div.onetrust-pc-dark-filter", # Overlay
                    "button.onetrust-close-btn-handler"
                ]
                for selector in cookie_selectors:
                    btns = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    if btns and btns[0].is_displayed():
                        Logger.info(f"Dismissing cookie banner ({selector})...")
                        self.browser.execute_script("arguments[0].click();", btns[0])
                
                # 2. Check for "Still listening?" popup
                popups = self.browser.find_elements(By.XPATH, "//*[contains(text(), 'Still listening') or contains(text(), 'Hala dinliyor musun')]")
                if popups:
                    Logger.info("Detected 'Still listening' popup. Attempting to dismiss...")
                    # Try clicking the play button or specific 'Yes' buttons if they appear
                    play_btns = self.browser.find_elements(By.CSS_SELECTOR, "button[data-testid='play-button']")
                    if play_btns:
                        self.browser.execute_script("arguments[0].click();", play_btns[0])
                        Logger.info("Clicked Play to dismiss 'Still listening'.")
                
            except Exception:
                pass 
            time.sleep(10) # Check every 10 seconds

    def start_loop(self, target_url):
        """Main automation loop for listening."""
        if not self.browser:
            Logger.error("Browser not launched!")
            return

        Logger.info(f"Starting automation loop for: {target_url}")
        self.running = True
        
        while self.running:
            try:
                current_url = self.browser.current_url
                
                # Check for first run or wrong page
                if target_url not in current_url:
                    Logger.info(f"Navigating to: {target_url}")
                    self.browser.get(target_url)
                    Humanizer.random_sleep(5, 8)
                    
                    # Detect premium on first successful load
                    if not hasattr(self, 'is_premium'):
                        self.is_premium = self._check_premium_status()
                
                # For FREE accounts, we MUST re-navigate every time at the START of the loop
                # because Spotify Free doesn't allow 'Repeat One' or it's unreliable.
                # However, if we JUST navigated (above), we don't need to do it again.
                elif not self.is_premium:
                    Logger.info("Free Account: Restarting song via navigation...")
                    self.browser.get(target_url)
                    Humanizer.random_sleep(5, 8)
                
                # 1. Click Play Button (if not already playing)
                self._click_play_button()
                
                # 2. Enable "Repeat One" mode (Only if Premium)
                if self.is_premium:
                    self._enable_repeat_one()
                else:
                    Logger.debug("Skipping Native Loop (Account is FREE)")
                
                # 3. Mute Spotify UI (Safety first)
                self._mute_spotify_ui()
                
                # 4. Verify and Log Metadata (Get duration)
                Humanizer.random_sleep(4, 6)
                is_playing, title, duration, _ = self._verify_playback(log_info=True)
                
                # 5. Listen for almost full duration
                if is_playing and duration > 0:
                    if self.is_premium:
                        # Premium: Can wait a bit longer, native loop handles it
                        listen_time = duration + random.uniform(-2, 5)
                        strategy = "Native Loop"
                    else:
                        # Free: MUST restart BEFORE it finishes to avoid shuffle/radio
                        listen_time = duration - random.uniform(2, 4)
                        if listen_time < 10: listen_time = duration # Safety for very short songs
                        strategy = "Free Re-nav Loop"
                    
                    Logger.info(f"{strategy} Active. Listening for {int(listen_time)}s until next cycle...")
                else:
                    listen_time = random.uniform(35, 60)
                    Logger.info(f"Fallback: Listening for {int(listen_time)} seconds...")
                
                start_wait = time.time()
                last_check = 0
                while time.time() - start_wait < listen_time:
                    if not self.running: break
                    
                    # For Free accounts, monitor playback progress aggressively
                    if not self.is_premium and time.time() - last_check > 5:
                        last_check = time.time()
                        # Quick check of playback state (Quiet mode)
                        is_now_playing, current_title, _, current_pos = self._verify_playback(log_info=False)
                        
                        # 1. Song Name Change Check
                        if is_now_playing and current_title != title and title != "Unknown Title":
                            Logger.warning(f"Song changed from '{title}' to '{current_title}'. Restarting early...")
                            break
                        
                        # 2. Position Check (Restart if within 5-8 seconds of the end)
                        if is_now_playing and duration > 0 and current_pos > 0:
                            if (duration - current_pos) <= 6:
                                Logger.info(f"Approaching end of song ({current_pos}s/{duration}s). Restarting early for Free account...")
                                break
                    
                    time.sleep(1)
                    if random.random() < 0.05:
                        Humanizer.perform_random_mouse_movements(self.browser, count=1)
                
                # 5. Periodic Visual Verification
                temp_browser = self.browser
                if self.running and temp_browser:
                    Logger.capture_screenshot(temp_browser, "visual_check")
                
                Logger.info(f"Listen cycle finished for {title}. Restarting for loop...")
                
            except Exception as e:
                Logger.error(f"Loop error: {e}")
                time.sleep(5)
            
            if not self.running: break

    def _verify_playback(self, log_info=True):
        """
        Extracts song metadata and verifies if it's actually playing.
        """
        if not self.browser:
            return False

        try:
            # 1. Extract Metadata (Title & Artist)
            title = "Unknown Title"
            artist = "Unknown Artist"
            
            try:
                # Priorities for Title: Bottom Player Bar > Page H1 > Generic Track Name
                title_selectors = [
                    "[data-testid='now-playing-widget'] [data-testid='track-info-name']", # Player Bar
                    "[data-testid='track-info-name']",
                    "div[data-testid='track-info-name'] a",
                    "h1[data-testid='entityTitle']", # Main page title
                    "h1", # Last resort H1
                ]
                
                # Phrases to ignore as titles (UI elements)
                blacklisted_titles = [
                    "install app", "premium", "login", 
                    "home", "search", "library",
                    "your library", "song", "artist", "views",
                    "explore premium", "queue", "liked songs", "liked",
                    "create playlist", "playlists", "albums", "podcasts"
                ]

                for selector in title_selectors:
                    if not self.browser: break
                    elems = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    for e in elems:
                        txt = e.text.strip()
                        if txt and len(txt) > 0:
                            # Check if text is blacklisted (Exact or common UI terms)
                            if txt.lower() in blacklisted_titles:
                                Logger.debug(f"Skipping generic UI text found in '{selector}': '{txt}'")
                                continue
                            title = txt
                            Logger.debug(f"Title MATCH found using '{selector}': {title}")
                            break
                    if title != "Unknown Title": break
                
                artist_selectors = [
                    "[data-testid='now-playing-widget'] [data-testid='track-info-artists']",
                    "[data-testid='track-info-artists']",
                    "[data-testid='creator-link']",
                    "div[data-testid='track-info-artists'] a",
                ]
                for selector in artist_selectors:
                    if not self.browser: break
                    elems = self.browser.find_elements(By.CSS_SELECTOR, selector)
                    if elems and elems[0].text.strip():
                        artist = elems[0].text.strip()
                        Logger.debug(f"Artist MATCH found using '{selector}': {artist}")
                        break
                        
                # Fallback to Page Title if still unknown
                if title == "Unknown Title" or artist == "Unknown Artist":
                    try:
                        page_title = self.browser.title
                        if " • " in page_title:
                            parts = page_title.split(" • ")
                            title = parts[0].strip()
                            artist = parts[1].split("|")[0].strip()
                    except: pass
            except:
                pass 
                
            if log_info:
                Logger.info(f"--- PLAYING: {title} by {artist} ---")

            # 2. Verify Playback State
            is_playing = False
            pause_indicators = [
                "button[data-testid='control-button-pause']",
                "button[aria-label='Pause']",
                "[data-testid='now-playing-menu'] [aria-label='Pause']",
                "button > svg > path[d*='M5.7 3h-1.4v18h1.4v-18zm8.3 0h-1.4v18h1.4v-18z']" # Universal Pause Path
            ]
            
            for selector in pause_indicators:
                if not self.browser: break
                elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                if elements and elements[0].is_displayed():
                    is_playing = True
                    Logger.debug(f"Active playback confirmed by pause indicator: '{selector}'")
                    break
            
            # 3. Extract Duration and Progress
            duration_sec = 0
            current_pos = 0
            try:
                # 3a. Duration
                duration_elem = self.browser.find_elements(By.CSS_SELECTOR, "[data-testid='playback-duration']")
                if duration_elem:
                    duration_str = duration_elem[0].text.strip()
                    duration_sec = self._parse_time(duration_str)
                    if duration_sec > 0:
                        Logger.debug(f"Track duration extracted: {duration_sec}s")
                
                # 3b. Progress (Position)
                pos_elem = self.browser.find_elements(By.CSS_SELECTOR, "[data-testid='playback-position']")
                if pos_elem:
                    pos_str = pos_elem[0].text.strip()
                    current_pos = self._parse_time(pos_str)
                    if current_pos > 0:
                        Logger.debug(f"Current playback position: {current_pos}s")
            except: pass

            if is_playing:
                if log_info:
                    Logger.info(f"VERIFIED: {title} is currently playing.")
            else:
                if log_info:
                    Logger.warning(f"VERIFICATION FAILED: Could not confirm playback for {title}. Check screenshots.")
                    Logger.capture_screenshot(self.browser, "verification_fail")
            
            return is_playing, title, duration_sec, current_pos

        except Exception as e:
            if self.browser: # Only log error if browser still exists
                Logger.debug(f"Verification Error: {e}")
            return False, "Unknown", 0, 0

    def _parse_time(self, time_str):
        """Helper to parse MM:SS or HH:MM:SS into seconds."""
        if not time_str or ":" not in time_str:
            return 0
        try:
            parts = [int(p) for p in time_str.split(":")]
            if len(parts) == 2: # MM:SS
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3: # HH:MM:SS
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
        except: pass
        return 0

    def _click_play_button(self):
        """Attempts multiple strategies to find and click the play button."""
        selectors = [
            "button[data-testid='play-button']", # Large Circle Play
            "button[data-testid='control-button-play']", # Bottom Bar Play
            "button[aria-label='Play']",
            "main button[aria-label*='Play']",
            "button > svg > path[d*='M7.05 3.606l13.49 7.79a.7.7 0 010 1.208l-13.49 7.79a.7.7 0 01-1.05-.604V4.21a.7.7 0 011.05-.604z']" # Play Path
        ]
        
        if not self.browser: return False

        # Debug info for the black screen issue
        try:
            curr_url = self.browser.current_url
            curr_title = self.browser.title
            Logger.debug(f"Searching for play button on: {curr_url} (Title: {curr_title})")
        except: pass

        # Try to find and click the first visible/active one
        for selector in selectors:
            try:
                elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                for btn in elements:
                    if btn.is_displayed():
                        label = btn.get_attribute("aria-label")
                        if label and "Pause" in label:
                            Logger.debug(f"Playback already active (indicated by button label: '{label}')")
                            return True
                            
                        # Double click protection or just direct click
                        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.5)
                        Logger.info(f"ACTION: Clicking play button found via '{selector}'")
                        self.browser.execute_script("arguments[0].click();", btn)
                        return True
            except: continue

        Logger.warning("Play button not found or already playing. Taking screenshot...")
        Logger.capture_screenshot(self.browser, "play_button_not_found")
        return False

    def _enable_repeat_one(self):
        """Clicks the repeat button until 'Repeat One' mode is active."""
        if not self.browser: return
        
        selector = "button[data-testid='control-button-repeat']"
        try:
            btn_elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
            if not btn_elements: return
            
            btn = btn_elements[0]
            # Common labels for "Repeat One"
            target_labels = ["Enable repeat one", "Repeat one"]
            
            # Max 3 clicks to cycle through Off -> All -> One
            for _ in range(3):
                label = btn.get_attribute("aria-label")
                if any(target.lower() in label.lower() for target in target_labels):
                    Logger.debug(f"Repeat One is already ACTIVE ('{label}')")
                    return
                
                Logger.debug(f"Current repeat state: '{label}'. Clicking for 'Repeat One'...")
                self.browser.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            
            Logger.info("Native 'Repeat One' loop enabled.")
        except Exception as e:
            Logger.debug(f"Could not enable Repeat One: {e}")

    def _mute_spotify_ui(self):
        """Clicks the mute button in Spotify UI if not already muted."""
        if not self.browser: return
        
        selector = "button[data-testid='control-button-mute']"
        try:
            btn_elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
            if not btn_elements: return
            
            btn = btn_elements[0]
            label = btn.get_attribute("aria-label")
            # Common labels for "Unmute" (meaning it's currently muted)
            muted_labels = ["Unmute"]
            
            if any(target.lower() in label.lower() for target in muted_labels):
                Logger.debug("Spotify UI is already MUTED.")
                return
                
            Logger.debug(f"Spotify UI is active ('{label}'). Clicking to MUTE...")
            self.browser.execute_script("arguments[0].click();", btn)
            Logger.info("Spotify UI volume muted.")
        except Exception as e:
            Logger.debug(f"Could not mute Spotify UI: {e}")

    def _check_premium_status(self):
        """Attempts to detect if the account is Premium or Free."""
        if not self.browser: return False
        
        Logger.info("Detecting account type (Premium vs Free)...")
        # Indicators for Free accounts (Upgrade buttons, etc.)
        selectors = [
            "button[data-testid='upgrade-button']",
            "a[href*='/premium']",
            "button[aria-label*='Premium']",
            "button[aria-label*='Upgrade']",
            "//*[contains(text(), 'Explore Premium')]"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    elems = self.browser.find_elements(By.XPATH, selector)
                else:
                    elems = self.browser.find_elements(By.CSS_SELECTOR, selector)
                
                for e in elems:
                    if e.is_displayed():
                        # Extra check: sometimes "Premium" is just in the name but not the button.
                        # We look for "Explore", "Upgrade", "Buy" etc.
                        txt = e.text.lower()
                        if any(x in txt for x in ["premium", "upgrade", "explore", "buy", "purchase"]):
                            Logger.info(f"Account Type: FREE (Indicator found: '{selector}')")
                            return False
            except: pass
            
        Logger.info("Account Type: PREMIUM (No upgrade indicators found)")
        return True

    def stop_session(self):
        """Gracefully stops all threads and closes browser."""
        Logger.info("Stopping bot session...")
        self.running = False
        temp_browser = self.browser
        self.browser = None # Set to None first to stop other threads
        
        if temp_browser:
            try:
                temp_browser.quit()
            except:
                pass
        Logger.info("Session stopped.")
