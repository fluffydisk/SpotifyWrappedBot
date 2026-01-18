import time
import random
from selenium.webdriver.common.action_chains import ActionChains

class Humanizer:
    """
    Provides methods to simulate human-like behavior (delays, mouse movements).
    """

    @staticmethod
    def random_sleep(min_seconds=1.0, max_seconds=3.0):
        """Sleeps for a random duration between min and max seconds."""
        duration = random.uniform(min_seconds, max_seconds)
        time.sleep(duration)

    @staticmethod
    def type_slowly(element, text, min_delay=0.05, max_delay=0.2):
        """Types text into an element one character at a time with random delays."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    @staticmethod
    def perform_random_mouse_movements(browser, count=3):
        """
        Simulates random mouse movements over the page using ActionChains.
        Note: This is 'invisible' mouse movement within the DOM context.
        """
        try:
            action = ActionChains(browser)
            viewport_width = browser.execute_script("return window.innerWidth;")
            viewport_height = browser.execute_script("return window.innerHeight;")
            
            for _ in range(count):
                x_offset = random.randint(0, int(viewport_width / 2))
                y_offset = random.randint(0, int(viewport_height / 2))
                
                # Move to a random offset from current position (or origin)
                # restricted to viewport roughly
                action.move_by_offset(x_offset, y_offset)
                action.pause(random.uniform(0.1, 0.5))
                # Move back to avoid drifting off infinitely
                action.move_by_offset(-x_offset, -y_offset) 
            
            action.perform()
        except Exception:
            # Ignore errors during random movements
            pass
