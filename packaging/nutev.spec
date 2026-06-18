# PyInstaller spec for the NutEV one-file Windows app.
# Build (from anywhere):  pyinstaller packaging/nutev.spec --noconfirm
# ruff: noqa  (PyInstaller injects SPECPATH/Analysis/PYZ/EXE at runtime)
import glob
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# SPECPATH is injected by PyInstaller = directory containing this spec (packaging/).
ROOT = os.path.dirname(SPECPATH)  # repo root

# Runtime data: every config/*.json (loaded via settings.config_root) and the
# dashboard template. Read from the repo at build time (no package-data needed).
datas = [(f, "config") for f in glob.glob(os.path.join(ROOT, "config", "*.json"))]
datas += [(os.path.join(ROOT, "src", "nutev", "api", "templates", "index.html"), "nutev/api/templates")]

# collect_submodules("nutev") guarantees lazily-imported modules (the pipeline,
# analysis, export, etc. are imported inside functions) end up in the bundle.
# uvicorn imports its loops/protocols/lifespan dynamically -> not visible statically.
hiddenimports = collect_submodules("nutev") + collect_submodules("uvicorn") + [
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "anyio._backends._asyncio",
]

# python-docx (optional Word export): bundle its default template + lxml backend.
try:
    datas += collect_data_files("docx")
    hiddenimports += collect_submodules("lxml")
except Exception:
    pass

a = Analysis(
    [os.path.join(SPECPATH, "nutev_app.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "streamlit", "torch", "faiss", "sentence_transformers"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NutEV",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep a console so users see the URL / errors
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
