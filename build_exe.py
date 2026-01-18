import PyInstaller.__main__
import os
import shutil

def build():
    print("Building SpotifyWrappedBot...")
    
    # Define arguments
    args = [
        'main.py',
        '--name=SpotifyWrappedBot',        # Name of the executable
        '--onedir',                        # Directory based build (easier for debugging)
        '--noconsole',                     # Hide console (GUI app)
        '--clean',                         # Clean cache
        '--add-data=src:src',              # Include source code if dynamically loaded
        '--add-data=assets:assets',        # Include assets
        '--hidden-import=customtkinter',   # Ensure CTk is found
        '--hidden-import=undetected_chromedriver',
        '--collect-all=customtkinter',     # Collect full package data
        '--log-level=INFO',
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    print("Build complete. Check 'dist/SpotifyWrappedBot/' folder.")

if __name__ == "__main__":
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    build()
