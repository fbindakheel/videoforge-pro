import os
import subprocess
import sys

def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def build_executable():
    print("=========================================")
    print("   Building VideoForge Pro Executable    ")
    print("=========================================")
    
    # Ensure PyInstaller is installed
    if not check_pyinstaller():
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Path to main.py
    main_script = "main.py"
    
    if not os.path.exists(main_script):
        print(f"Error: {main_script} not found in the current directory.")
        sys.exit(1)

    # PyInstaller arguments
    args = [
        "pyinstaller",
        "--noconfirm",         # Overwrite output directory without asking
        "--onedir",            # Create a one-folder bundle (faster startup than onefile)
        "--windowed",          # Don't show a console window (GUI app)
        "--name", "VideoForge-Pro", # Name of the executable
        # Exclude unnecessary modules to reduce size
        "--exclude-module", "tkinter", 
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "numpy_financial",
        # Explicitly add the app package
        "--add-data", "app;app", 
        main_script
    ]

    print(f"Running PyInstaller recursively with args: {' '.join(args)}")
    
    try:
        # Run PyInstaller
        subprocess.check_call(args)
        print("\n=========================================")
        print("   Build Successful!                      ")
        print("   Executable located in: dist/VideoForge-Pro/ ")
        print("=========================================")
    except subprocess.CalledProcessError as e:
        print(f"\n=========================================")
        print(f"   Build Failed!                         ")
        print(f"   Error code: {e.returncode}            ")
        print(f"=========================================")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
