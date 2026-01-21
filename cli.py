#!/usr/bin/env python3
"""
Spotify Automation Bot - CLI Version
Cross-platform command-line interface
"""

import argparse
import sys
from src.cli.cli_interface import CLI

def main():
    parser = argparse.ArgumentParser(
        description="Spotify Automation Bot - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py login                              # Import cookies to authenticate
  python cli.py start URL                          # Start automation
  python cli.py start URL --headless               # Start in headless mode
  python cli.py stats                              # Display statistics
  python cli.py logout                             # Clear session

For more information, visit: https://github.com/yourusername/SpotifyWrappedBot
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Login command
    subparsers.add_parser('login', help='Import cookies to authenticate with Spotify')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start automation for a Spotify URL')
    start_parser.add_argument('url', help='Spotify track or playlist URL')
    start_parser.add_argument('--headless', action='store_true', help='Run browser in headless mode (no window)')
    start_parser.add_argument('--repeat', type=int, default=0, help='Number of times to repeat (0 = infinite)')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop running automation')
    
    # Stats command
    subparsers.add_parser('stats', help='Display listening statistics')
    
    # Logout command
    subparsers.add_parser('logout', help='Clear session and delete cookies')
    
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Run CLI
    cli = CLI()
    try:
        cli.run(args)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
