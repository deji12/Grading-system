import PyInstaller.__main__
import os
import sys

# Create version info file
version_info = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'Ayodeji Adesola'),
           StringStruct(u'FileDescription', u'Grading Application'),
           StringStruct(u'FileVersion', u'1.0.0.0'),
           StringStruct(u'LegalCopyright', u'Copyright (c) 2026 Ayodeji Adesola'),
           StringStruct(u'OriginalFilename', u'GradingApp.exe'),
           StringStruct(u'ProductName', u'Grading Application'),
           StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

with open('version.txt', 'w') as f:
    f.write(version_info)

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
    '--noconsole',  # Changed from --console to --noconsole to hide terminal
    '--version-file=version.txt',
    # '--uac-admin',  # Optional: Request admin privileges if needed
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
print("📌 Note: The executable will now run without a terminal window.")