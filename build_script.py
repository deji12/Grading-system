import PyInstaller.__main__
import os
import sys

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# List all your Python files
python_files = [
    'main.py',
    'ui.py', 
    'formatter.py',
    'utils.py',
    'grade_calculations.py',
]

# Create the PyInstaller command
pyinstaller_args = [
    '--onefile',
    '--name=GradingApp',
    '--console',  # Remove this if you don't want console window
]

# Add all Python files as separate arguments
pyinstaller_args.extend(python_files)

# Add config.json as data file
pyinstaller_args.append('--add-data=config.json;.')

# Add hidden imports for customtkinter if needed
pyinstaller_args.append('--hidden-import=customtkinter')
pyinstaller_args.append('--hidden-import=tkinter')

# Run PyInstaller
PyInstaller.__main__.run(pyinstaller_args)

print("\n✅ Build complete! Executable is in the 'dist' folder.")