import sys
import multiprocessing
from src.utils.logger import Logger
from src.ui.main_window import MainWindow

# TODO: Load configuration from config/settings.json

def main():
    """
    Main entry point for the Spotify Wrapped Bot application.
    """
    multiprocessing.freeze_support()
    
    # Initialize Logger
    Logger.init()
    Logger.info("Application starting...")

    # TODO: Perform initial license check or HWID validation here or within the GUI
    
    # Initialize and run the GUI
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()