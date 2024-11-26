import os
import sys
import subprocess

def build_executable():
    # Determine the script name
    script_name = 'main.py'  # Your main script name

    # PyInstaller command with additional options
    pyinstaller_cmd = [
        'pyinstaller',
        '--onefile',               # Single executable
        '--windowed',              # No console window
        '--name', 'RFIDReader',    # Output executable name
        # '--add-data', 'path/to/additional/resources:.',  # Add any additional resources
        # '--icon', 'path/to/icon.ico',  # Optional: Add an application icon
        script_name
    ]

    try:
        # Run PyInstaller
        subprocess.run(pyinstaller_cmd, check=True)
        print("Build completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    build_executable()