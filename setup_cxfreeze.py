import sys
from cx_Freeze import setup, Executable

# Opções de build
build_exe_options = {
    "packages": [
        "os",
        "shutil",
        "math",
        "subprocess",
        "threading",
        "ctypes",
        "tkinter",
        "just_playback",
        "pytubefix",
        "librosa",
        "pydub",
        "PIL",
        "chord_extractor",
        "datatypes"
    ],
    "includes": [
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "PIL.Image",
        "PIL.ImageTk",
        "PIL._tkinter_finder",
        "chord_extractor.extractors",
        "datatypes.chord",
        "just_playback",
        "pytubefix",
        "librosa",
        "pydub"
    ],
    "include_files": [
        "chords_diagram",
        "datatypes",
        "images",
        "vamp"
    ],
    "excludes": [],
}

# Base do executável: None = console, Win32GUI = sem console no Windows
base = None


setup(
    name="ChordOPython",
    version="1.0",
    description="ChordOPython",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
