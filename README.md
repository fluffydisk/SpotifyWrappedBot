# Spotify Wrapped Bot 🎧

A robust, GUI-based Spotify automation bot designed for controlled listening and stream management. It supports both Free and Premium accounts with adaptive looping strategies.

## ✨ Features

- **Native Looping:** Uses Spotify's "Repeat One" feature for Premium accounts.
- **Smart Re-navigation:** Adaptive looping for Free accounts by re-navigating before song ends.
- **Seamless Login:** Supports manual login with session persistence to bypass bot detection.
- **Dual Muting:** Mutes audio at both browser and Spotify UI levels for silent operation.
- **Humanized Interaction:** Randomized mouse movements and search delays to mimic human behavior.
- **Headless Mode:** Run the bot in the background without a browser window.
- **Visual Logs:** Automatically captures screenshots on verification failures or errors.

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SpotifyWrapped.git
   cd SpotifyWrapped
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠 Usage

Start the GUI application:
```bash
python3 main.py
```

1. **Login:** Click the "Login" button. A browser window will open. Login to your Spotify account and close the window once done.
2. **Start Bot:** Enter the Spotify Track URL and click "Start Automation".

## ⚠️ Disclaimer

This tool is for educational purposes only. Use of automation bots may violate Spotify's Terms of Service. Use at your own risk.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details. (Create one if needed)
