#!/usr/bin/env python3

from pathlib import Path
import shutil

HOME = Path.home()


LA_VIPERA = HOME / "La_Vipera"
SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_PROGRAM = SCRIPT_DIR / "src" / "la-vipera.py"

APP_DIR = LA_VIPERA / "app"
APP_PROGRAM = APP_DIR / "la-vipera.py"

LOCAL_BIN = HOME / ".local" / "bin"
LAUNCHER = LOCAL_BIN / "la-vipera"

OWNERSHIP_MARKER = LA_VIPERA / ".la_vipera"

WORKSPACE = LA_VIPERA / "workspace"
INCOMING = WORKSPACE / "incoming"
ARCHIVE = WORKSPACE / "archive"
BACKUPS = WORKSPACE / "backups"
QUARANTINE = WORKSPACE / "quarantine"

LIBRARIES = LA_VIPERA / "libraries"
SYMBOL_LIBRARY = LIBRARIES / "La_Vipera.kicad_sym"
FOOTPRINT_LIBRARY = LIBRARIES / "La_Vipera.pretty"
MODEL_LIBRARY = LIBRARIES / "La_Vipera.3dshapes"


def create_directory(path):
    if path.exists():
        print(f"Exists:  {path}")
        return

    path.mkdir(parents=True)
    print(f"Created: {path}")


def create_symbol_library(path):
    if path.exists():
        print(f"Exists:  {path}")
        return

    content = """(kicad_symbol_lib (version 20231120) (generator kicad_symbol_editor)
)
"""

    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")

def prepare_workspace():
    if LA_VIPERA.exists():
        if not LA_VIPERA.is_dir():
            print(f"ERROR: {LA_VIPERA} exists but is not a directory.")
            return False

        if not valid_ownership_marker():
            print(f"ERROR: {LA_VIPERA} already exists but is not")
            print("recognised as a La Vipera workspace.")
            print()
            print("No changes have been made.")
            return False

        print(f"Workspace: {LA_VIPERA}")
        return True

    LA_VIPERA.mkdir()
    OWNERSHIP_MARKER.write_text("La Vipera Publica\n", encoding="utf-8")

    print(f"Created: {LA_VIPERA}")
    print(f"Created: {OWNERSHIP_MARKER}")
    return True

def valid_ownership_marker():
    if not OWNERSHIP_MARKER.is_file():
        return False

    try:
        content = OWNERSHIP_MARKER.read_text(encoding="utf-8").strip()
    except OSError:
        return False

    return content == "La Vipera Publica"

def install_program():
    """Install the La Vipera application."""

    if not SOURCE_PROGRAM.is_file():
        print(f"ERROR: Application source not found: {SOURCE_PROGRAM}")
        return False

    create_directory(APP_DIR)

    shutil.copy2(SOURCE_PROGRAM, APP_PROGRAM)
    APP_PROGRAM.chmod(0o755)

    print(f"Installed: {APP_PROGRAM}")
    return True

def install_launcher():
    """Install the la-vipera command."""

    create_directory(LOCAL_BIN)

    content = f"""#!/bin/sh
exec "{APP_PROGRAM}" "$@"
"""

    LAUNCHER.write_text(content, encoding="utf-8")
    LAUNCHER.chmod(0o755)

    print(f"Installed: {LAUNCHER}")


def main():
    print("La Vipera Publica installer")
    print("---------------------------")

    if not prepare_workspace():
        return

    print()

    create_directory(INCOMING)
    create_directory(ARCHIVE)
    create_directory(BACKUPS)
    create_directory(QUARANTINE)

    create_directory(LIBRARIES)
    create_directory(FOOTPRINT_LIBRARY)
    create_directory(MODEL_LIBRARY)

    create_symbol_library(SYMBOL_LIBRARY)

    print()

    if not install_program():
        return

    install_launcher()

    print()
    print("La Vipera Publica installed.")
    print()
    print("To make the la-vipera command available in this terminal, run:")
    print()
    print("  source ~/.profile")
    print()
    print("Then run:")
    print()
    print("  la-vipera")

if __name__ == "__main__":
    main()
