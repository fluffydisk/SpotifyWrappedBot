class SpotifySelectors:
    """
    Centralized CSS selectors for Spotify web elements.
    """
    # Playback Controls
    PLAY_BUTTON = "button[data-testid='play-button']"
    PAUSE_BUTTON = "button[data-testid='play-button'][aria-label='Pause']" # Often same ID, diff label
    REPLAY_BUTTON = "button[data-testid='control-button-repeat']"
    
    # Progress/Time
    PLAYBACK_POSITION = "div[data-testid='playback-position']"
    PLAYBACK_DURATION = "div[data-testid='playback-duration']"
    PROGRESS_BAR = "div[data-testid='progress-bar']"
    
    # Popups / Alerts
    STILL_LISTENING_MODAL = ".GenericModal" # Example class, needs verification
    MODAL_CLOSE_BUTTON = "button[aria-label='Close']"
    
    # Login Indicators
    USER_WIDGET = "button[data-testid='user-widget-link']"
    LOGIN_BUTTON = "button[data-testid='login-button']"
