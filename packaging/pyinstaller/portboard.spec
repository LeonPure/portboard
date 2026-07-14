# ruff: noqa: F821

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parents[1]

analysis = Analysis(
    [str(PROJECT_ROOT / "src" / "portboard" / "__main__.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=[
        (
            str(
                PROJECT_ROOT
                / "src"
                / "portboard"
                / "presentation"
                / "tui"
                / "portboard.tcss"
            ),
            "portboard/presentation/tui",
        )
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="portboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
