"""CLI Interface - Command handlers"""
import time
import signal
import sys
from colorama import init, Fore, Style
from src.cli.session import CLISession
from src.core.browser_mgr import BrowserManager
from src.core.bot_engine import SpotifyBot
from src.core.stats_manager import StatisticsManager

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class CLI:
    """Command-line interface for Spotify Automation Bot"""
    
    def __init__(self):
        self.bot = None
        self.running = False
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
        if self.bot and self.running:
            print(f"{Fore.CYAN}[*] Stopping bot...{Style.RESET_ALL}")
            self.bot.stop_session()
        sys.exit(0)
    
    def run(self, args):
        """Execute command based on arguments"""
        command = args.command
        
        if command == 'login':
            self.cmd_login()
        elif command == 'start':
            self.cmd_start(args.url, args.headless, args.repeat)
        elif command == 'stop':
            self.cmd_stop()
        elif command == 'stats':
            self.cmd_stats()
        elif command == 'logout':
            self.cmd_logout()
    
    def cmd_login(self):
        """Interactive cookie import"""
        print(f"\n{Fore.CYAN}[*] Spotify Authentication - Cookie Import{Style.RESET_ALL}")
        print("=" * 50)
        print("\nTo authenticate, import cookies from your browser:\n")
        print("Steps:")
        print("  1. Open https://open.spotify.com in your browser")
        print("  2. Sign in with your account (Google/Facebook/Apple/Email)")
        print("  3. Press F12 -> Application -> Cookies -> https://open.spotify.com")
        print("  4. Copy the values of sp_dc and sp_key cookies\n")
        
        sp_dc = input(f"{Fore.YELLOW}Enter sp_dc value: {Style.RESET_ALL}").strip()
        sp_key = input(f"{Fore.YELLOW}Enter sp_key value: {Style.RESET_ALL}").strip()
        
        # Validate
        if not sp_dc or len(sp_dc) < 10:
            print(f"{Fore.RED}[X] Invalid sp_dc cookie (too short){Style.RESET_ALL}")
            return
        
        if not sp_key or len(sp_key) < 5:
            print(f"{Fore.RED}[X] Invalid sp_key cookie (too short){Style.RESET_ALL}")
            return
        
        # Create cookie structure
        cookies = [
            {
                "name": "sp_dc",
                "value": sp_dc,
                "domain": ".spotify.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            },
            {
                "name": "sp_key",
                "value": sp_key,
                "domain": ".spotify.com",
                "path": "/",
                "secure": True,
                "httpOnly": False
            }
        ]
        
        # Save using existing BrowserManager
        if BrowserManager.save_cookies(cookies):
            print(f"\n{Fore.GREEN}[OK] Cookies validated successfully!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[OK] Session saved{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.RED}[X] Failed to save cookies{Style.RESET_ALL}\n")
    
    def cmd_start(self, url, headless=True, repeat=0):
        """Start automation with real-time updates"""
        # Check authentication
        CLISession.require_login()
        
        print(f"\n{Fore.CYAN}[*] Starting Automation{Style.RESET_ALL}")
        print("=" * 50)
        print(f"Target: {url}")
        print(f"Mode: {'Headless' if headless else 'Visible Browser'}")
        print(f"Repeat: {'Infinite' if repeat == 0 else repeat}\n")
        
        # Initialize bot
        self.bot = SpotifyBot({"profile_dir": "spotify_profile"})
        
        try:
            # Launch browser
            print(f"{Fore.CYAN}[*] Launching browser...{Style.RESET_ALL}")
            self.bot.launch_browser(headless=headless)
            print(f"{Fore.GREEN}[OK] Browser launched{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[OK] Cookies loaded{Style.RESET_ALL}")
            
            # Start automation
            print(f"{Fore.CYAN}[*] Starting playback...{Style.RESET_ALL}")
            self.bot.start_automation(url, repeat_count=repeat)
            print(f"{Fore.GREEN}[OK] Playback started{Style.RESET_ALL}\n")
            
            self.running = True
            print(f"{Fore.YELLOW}Press Ctrl+C to stop...{Style.RESET_ALL}\n")
            
            # Keep alive and show status
            while self.bot.running:
                time.sleep(2)
                # Could add live status updates here
            
        except KeyboardInterrupt:
            raise  # Re-raise to be handled by signal handler
        except Exception as e:
            print(f"\n{Fore.RED}[X] Error: {e}{Style.RESET_ALL}")
            if self.bot:
                self.bot.stop_session()
    
    def cmd_stop(self):
        """Stop running automation"""
        if self.bot and self.running:
            print(f"\n{Fore.CYAN}[*] Stopping automation...{Style.RESET_ALL}")
            self.bot.stop_session()
            self.running = False
            print(f"{Fore.GREEN}[OK] Stopped{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.YELLOW}[!] No automation is currently running{Style.RESET_ALL}\n")
    
    def cmd_stats(self):
        """Display formatted statistics"""
        stats = StatisticsManager()
        all_stats = stats.get_all_stats()
        
        print(f"\n{Fore.CYAN}[*] Listening Statistics{Style.RESET_ALL}")
        print("=" * 50)
        print(f"\n{Fore.GREEN}Total Listening Time:{Style.RESET_ALL} {all_stats['total_time']}")
        print(f"{Fore.GREEN}Unique Songs Played:{Style.RESET_ALL} {all_stats['song_count']}")
        
        if all_stats['top_songs']:
            print(f"\n{Fore.CYAN}[*] Top Songs:{Style.RESET_ALL}")
            for i, song in enumerate(all_stats['top_songs'][:10], 1):
                # Color top 3 differently
                rank_color = Fore.YELLOW if i <= 3 else Fore.WHITE
                print(f"  {rank_color}#{i}{Style.RESET_ALL} {song['name']} - {Fore.CYAN}{song['artist']}{Style.RESET_ALL}")
                print(f"     {Fore.GREEN}{song['play_count']} plays{Style.RESET_ALL} | {song['total_time']}")
        else:
            print(f"\n{Fore.YELLOW}No listening data yet. Start playing some music!{Style.RESET_ALL}")
        
        print()  # Empty line at end
    
    def cmd_logout(self):
        """Clear session and delete cookies"""
        if CLISession.clear_session():
            print(f"\n{Fore.GREEN}[OK] Session cleared{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[OK] Cookies deleted{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.YELLOW}[!] No session to clear{Style.RESET_ALL}\n")
