import os
import sys
import numpy
import scipy
import numba
import llvmlite
import librosa
import easy_pil
from cx_Freeze import setup, Executable

try:
    import lazy_loader
    lazy_loader.attach_stub = lambda *a, **k: None
except Exception:
    pass

def include_if_exists(src, dest):
    """Devuelve una tupla (src, dest) si el archivo existe, de lo contrario None."""
    if os.path.exists(src):
        return (src, dest)
    return None

# Definir las opciones para el archivo ejecutable
build_exe_options = {
    "packages": [
        "os",
        "easy_pil",
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
        "datatypes",
        "audioread",
        "decorator",
        "joblib",
        "lazy_loader",
        "msgpack",
        "numba",
        "numpy",
        "pooch",
        "scipy",
        "soundfile",
        "soxr",
        "typing_extensions",
        "certifi",
        "cffi",
        "charset_normalizer",
        "idna",
        "llvmlite",
        "packaging",
        "platformdirs",
        "pycparser",
        "requests",
        "threadpoolctl",
        "urllib3",
    ],
    "includes": [
        "tkinter",
        "easy_pil",
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
        "pydub",
        "librosa.core",
        "librosa.display",
        "librosa.effects",
        "librosa.feature",
        "librosa.onset",
        "librosa.beat",
        "librosa.decompose",
        "librosa.segment",
        "librosa.util",
        "scipy.fft",
        "scipy.io",
        "scipy.signal",
        "scipy.spatial",
        "scipy.stats",
    ],
    "include_files": [
        "chords_diagram",
        "datatypes",
        "images",
        "vamp",
        (os.path.join(numpy.__path__[0], "_core"), "lib/numpy/_core"),
        (os.path.join(scipy.__path__[0], "_lib"), "lib/scipy/_lib"),
        (os.path.join(numba.__path__[0], "misc"), "lib/numba/misc"),
        (os.path.join(llvmlite.__path__[0], "binding"), "lib/llvmlite/binding"),
        include_if_exists(os.path.join(numpy.__path__[0], ".libs"), "lib/numpy/.libs"),
        include_if_exists(os.path.join(librosa.__path__[0], "__init__.pyi"), "lib/librosa/__init__.pyi"),
    ],
    "excludes": [],
    "include_msvcr": True,
}

# Filtrar cualquier None de 'include_files' para evitar problemas
build_exe_options["include_files"] = [
    item for item in build_exe_options["include_files"] if item is not None
]

# Si el sistema operativo es Windows, se usa la base 'Win32GUI'
base = None


# Configuración del script cx_Freeze
setup(
    name="ChordOPython",
    version="1.0",
    description="ChordOPython",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
