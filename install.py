#!/usr/bin/env python3

from pathlib import Path


HOME = Path.home()

LA_VIPERA = HOME / "La_Vipera"

WORKSPACE = LA_VIPERA / "workspace"
INCOMING = WORKSPACE / "incoming"
ARCHIVE = WORKSPACE / "archive"
BACKUPS = WORKSPACE / "backups"

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


def main():
    print("La Vipera Publica installer")
    print("---------------------------")

    create_directory(INCOMING)
    create_directory(ARCHIVE)
    create_directory(BACKUPS)

    create_directory(LIBRARIES)
    create_directory(FOOTPRINT_LIBRARY)
    create_directory(MODEL_LIBRARY)

    create_symbol_library(SYMBOL_LIBRARY)

    print()
    print("La Vipera skeleton ready.")


if __name__ == "__main__":
    main()
