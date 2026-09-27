#!/usr/bin/env python3

from pathlib import Path
import re
import zipfile
import readline
import shutil
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMPORT_DIR = Path.home() / "kicad_import"
INCOMING_DIR = IMPORT_DIR / "incoming"

FOOTPRINT_DIR = Path.home() / "kicad_footprints" / "armadillo.pretty"
MODEL_DIR = Path.home() / "kicad_3dmodels" / "custom.3dshapes"

MODEL_KICAD_PREFIX = "${MY_3DMODELS}/custom.3dshapes"

SYMBOL_DIR = Path.home() / "kicad_library"

ARCHIVE_DIR = IMPORT_DIR / "archive"
BACKUP_DIR = IMPORT_DIR / "backups"


def find_zip_files():
    """Return ZIP files waiting in the incoming directory."""
    return sorted(INCOMING_DIR.glob("*.zip"))


def classify_member(name):
    """Classify a file contained in a component ZIP."""
    suffix = Path(name).suffix.lower()

    if suffix == ".kicad_sym":
        return "symbol"

    if suffix == ".kicad_mod":
        return "footprint"

    if suffix in (".step", ".stp"):
        return "model"

    return "other"


def inspect_symbol(text):
    """Extract useful information from a KiCad symbol library."""

    result = {
        "name": None,
        "value": None,
        "footprint": None,
    }

    match = re.search(r'\(symbol\s+"([^"]+)"', text)
    if match:
        result["name"] = match.group(1)

    match = re.search(r'\(property\s+"Value"\s+"([^"]*)"', text)
    if match:
        result["value"] = match.group(1)

    match = re.search(r'\(property\s+"Footprint"\s+"([^"]*)"', text)
    if match:
        result["footprint"] = match.group(1)

    return result


def inspect_footprint(text):
    """Extract useful information from a KiCad footprint."""

    result = {
        "name": None,
        "value": None,
    }

    match = re.search(
        r'\(footprint\s+(?:"([^"]+)"|([^\s()]+))',
        text,
    )
    if match:
        result["name"] = match.group(1) or match.group(2)

    match = re.search(
        r'\(fp_text\s+value\s+(?:"([^"]+)"|([^\s()]+))',
        text
    )
    if match:
        result["value"] = match.group(1) or match.group(2)

    return result


def inspect_zip(zip_path):
    """Inspect a ZIP without extracting or modifying anything."""

    contents = {
        "symbols": [],
        "footprints": [],
        "models": [],
        "other": [],
    }

    with zipfile.ZipFile(zip_path, "r") as archive:

        for member in archive.infolist():

            if member.is_dir():
                continue

            category = classify_member(member.filename)

            if category == "symbol":
                text = archive.read(member).decode(
                    "utf-8", errors="replace"
                )

                info = inspect_symbol(text)
                info["file"] = member.filename
                contents["symbols"].append(info)

            elif category == "footprint":
                text = archive.read(member).decode(
                    "utf-8", errors="replace"
                )

                info = inspect_footprint(text)
                info["file"] = member.filename
                contents["footprints"].append(info)

            elif category == "model":
                contents["models"].append(member.filename)

            else:
                contents["other"].append(member.filename)

    return contents


def display_contents(contents):
    """Display interpreted ZIP contents."""

    print()

    print(f"Symbols: {len(contents['symbols'])}")

    for symbol in contents["symbols"]:
        print(f"  File:      {Path(symbol['file']).name}")
        print(f"  Name:      {symbol['name']}")
        print(f"  Value:     {symbol['value']}")
        print(f"  Footprint: {symbol['footprint']}")
        print()

    preferred_footprints = {
        symbol["footprint"]
        for symbol in contents["symbols"]
        if symbol["footprint"]
    }

    print(f"Footprints: {len(contents['footprints'])}")

    for footprint in contents["footprints"]:

        file_stem = Path(footprint["file"]).stem
        preferred = ""

        if file_stem in preferred_footprints:
            preferred = "  [symbol default]"

        print(f"  File:  {Path(footprint['file']).name}")
        print(f"  Name:  {footprint['name']}{preferred}")
        print(f"  Value: {footprint['value']}")
        print()

    print(f"3D models: {len(contents['models'])}")

    for model in contents["models"]:
        print(f"  {Path(model).name}")

    print()

    print(f"Other files: {len(contents['other'])}")

    for filename in contents["other"]:
        print(f"  {filename}")

    print()


def choose_footprint(contents):
    """Allow the user to select a footprint."""

    footprints = contents["footprints"]

    if not footprints:
        return None

    preferred_names = {
        symbol["footprint"]
        for symbol in contents["symbols"]
        if symbol["footprint"]
    }

    default_index = 0

    for index, footprint in enumerate(footprints):
        if Path(footprint["file"]).stem in preferred_names:
            default_index = index
            break

    print("Select footprint:\n")

    for number, footprint in enumerate(footprints, start=1):

        stem = Path(footprint["file"]).stem
        marker = ""

        if number - 1 == default_index:
            marker = "  [default]"

        print(f"  {number}) {stem}{marker}")

    print("  0) None")

    print()

    while True:

        choice = input(
            f"Selection [{default_index + 1}]: "
        ).strip()

        if choice == "":
            return footprints[default_index]

        try:
            selection = int(choice)

            if selection == 0:
                return None

            if 1 <= selection <= len(footprints):
                return footprints[selection - 1]

        except ValueError:
            pass

        print("Invalid selection.")


def ask_name(prompt, default):
    """Ask for a production name with an editable default."""

    while True:

        def prefill():
            readline.insert_text(default)
            readline.redisplay()

        readline.set_pre_input_hook(prefill)

        try:
            value = input(f"{prompt}: ").strip()
        finally:
            readline.set_pre_input_hook(None)

        if value:
            return value

        print("A name is required.")        

def ask_yes_no(prompt, default=True):
    """Ask a yes/no question."""

    if default:
        suffix = "[Y/n]"
    else:
        suffix = "[y/N]"

    while True:

        answer = input(f"{prompt} {suffix}: ").strip().lower()

        if answer == "":
            return default

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please answer y or n.")


def build_proposal(contents):
    """Ask the user what should eventually be promoted."""

    proposal = {
        "symbol": None,
        "symbol_name": None,
        "symbol_library": None,
        "use_existing_symbol": False,
        "footprint": None,
        "footprint_name": None,
        "use_existing_footprint": False,
        "model": None,
        "link_model": False,
    }
    print()
    print("Import choices")
    print("--------------")
    print()

    # Symbol ---------------------------------------------------------------

    if contents["symbols"]:

        symbol = contents["symbols"][0]

        default_name = (
            symbol["name"]
            or symbol["value"]
            or Path(symbol["file"]).stem
        )

        proposal["symbol"] = symbol
        proposal["symbol_name"] = ask_name(
            "Production symbol name",
            default_name
        )

        print()

    # Footprint ------------------------------------------------------------

    footprint = choose_footprint(contents)

    if footprint:

        default_name = Path(footprint["file"]).stem

        proposal["footprint"] = footprint
        proposal["footprint_name"] = ask_name(
            "Production footprint name",
            default_name
        )

        production_path = (
            FOOTPRINT_DIR
            / f"{proposal['footprint_name']}.kicad_mod"
        )

        if production_path.exists():
            print()
            print("Production footprint already exists:")
            print(f"  {production_path}")
            print()

            proposal["use_existing_footprint"] = ask_yes_no(
                "Use existing production footprint?",
                default=True
            )

        print()
        
    # 3D model -------------------------------------------------------------

    models = contents["models"]

    if models:

        if len(models) == 1:
            model = models[0]

        else:
            print("Select 3D model:\n")

            for number, model_name in enumerate(models, start=1):
                print(f"  {number}) {Path(model_name).name}")

            print("  0) None")
            print()

            while True:

                choice = input("Selection [1]: ").strip()

                if choice == "":
                    model = models[0]
                    break

                try:
                    selection = int(choice)

                    if selection == 0:
                        model = None
                        break

                    if 1 <= selection <= len(models):
                        model = models[selection - 1]
                        break

                except ValueError:
                    pass

                print("Invalid selection.")

        proposal["model"] = model

        if model and proposal["footprint"]:

            print()
            proposal["link_model"] = ask_yes_no(
                "Link 3D model to selected footprint?",
                default=True
            )

    if proposal["symbol"]:
        print()
        proposal["symbol_library"] = choose_symbol_library()

        if symbol_exists_in_library(
            proposal["symbol_library"],
            proposal["symbol_name"],
        ):
            print()
            print("Production symbol already exists:")
            print(
                f"  {proposal['symbol_library'].stem}:"
                f"{proposal['symbol_name']}"
            )
            print()

            proposal["use_existing_symbol"] = ask_yes_no(
                "Use existing production symbol?",
                default=True
            )

            if (
                proposal["use_existing_symbol"]
                and proposal["footprint"]
            ):
                existing_footprint = get_symbol_footprint(
                    proposal["symbol_library"],
                    proposal["symbol_name"],
                )

                expected_footprint = (
                    f"armadillo:{proposal['footprint_name']}"
                )

                if existing_footprint != expected_footprint:
                    print()
                    print(
                        "WARNING — EXISTING SYMBOL FOOTPRINT MISMATCH"
                    )
                    print()
                    print(
                        "Existing symbol Footprint property:"
                    )
                    print(f"  {existing_footprint or '(none)'}")
                    print()
                    print("Selected production footprint:")
                    print(f"  {expected_footprint}")
                    print()
                    print(
                        "The existing symbol will NOT be modified."
                    )
                    print()

                    if not ask_yes_no(
                        "Continue using existing symbol?",
                        default=False,
                    ):
                        proposal["use_existing_symbol"] = False


    return proposal

def find_symbol_libraries():
    """Return top-level production symbol libraries."""
    return sorted(SYMBOL_DIR.glob("*.kicad_sym"))


def choose_symbol_library():
    """Allow the user to choose a production symbol library."""

    libraries = find_symbol_libraries()

    if not libraries:
        raise RuntimeError(
            f"No production .kicad_sym libraries found in {SYMBOL_DIR}"
        )

    print("Select destination symbol library:\n")

    for number, library in enumerate(libraries, start=1):
        print(f"  {number}) {library.name}")

    print()

    while True:
        choice = input("Selection [1]: ").strip()

        if choice == "":
            return libraries[0]

        try:
            selection = int(choice)
            if 1 <= selection <= len(libraries):
                return libraries[selection - 1]
        except ValueError:
            pass

        print("Invalid selection.")


def symbol_exists_in_library(library_path, symbol_name):
    """Return True if the target already contains the root symbol."""
    library_text = library_path.read_text(
        encoding="utf-8", errors="replace"
    )
    pattern = r'\(symbol\s+"' + re.escape(symbol_name) + r'"\s'
    return re.search(pattern, library_text) is not None


def get_symbol_footprint(library_path, symbol_name):
    """Return the Footprint property of an existing root symbol."""

    text = library_path.read_text(
        encoding="utf-8", errors="replace"
    )

    pattern = (
        r'\(symbol\s+"'
        + re.escape(symbol_name)
        + r'"\s'
    )

    match = re.search(pattern, text)

    if not match:
        return None

    start = match.start()
    next_symbol = re.search(r'\n\s*\(symbol\s+"', text[match.end():])

    if next_symbol:
        end = match.end() + next_symbol.start()
        symbol_text = text[start:end]
    else:
        symbol_text = text[start:]

    footprint = re.search(
        r'\(property\s+"Footprint"\s+"([^"]*)"',
        symbol_text,
    )

    if footprint:
        return footprint.group(1)

    return None


def _sexpr_depth_delta(text):
    """Return parenthesis depth change, ignoring parentheses in strings."""
    depth = 0
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1

    return depth


def extract_symbols(text):
    """Return top-level symbol blocks from a KiCad symbol library."""
    symbols = []
    lines = text.splitlines(keepends=True)
    library_depth = 0
    start = None
    symbol_depth = 0

    for index, line in enumerate(lines):
        stripped = line.lstrip()

        if (
            start is None
            and library_depth == 1
            and stripped.startswith("(symbol ")
        ):
            start = index
            symbol_depth = 0

        delta = _sexpr_depth_delta(line)

        if start is not None:
            symbol_depth += delta
            if symbol_depth == 0:
                symbols.append("".join(lines[start:index + 1]))
                start = None

        library_depth += delta

    if start is not None:
        raise RuntimeError("Incomplete symbol block in KiCad symbol library.")

    return symbols


def symbol_block_name(symbol_text):
    """Return the name from a top-level KiCad symbol block."""
    first_line = symbol_text.splitlines()[0]

    match = re.search(r'\(symbol\s+"([^"]+)"', first_line)
    if match:
        return match.group(1)

    match = re.search(r'\(symbol\s+([^\s()]+)', first_line)
    return match.group(1) if match else None


def merge_symbol_text(source_text, target_path):
    """Append new top-level symbols while preserving the target library."""
    target_text = target_path.read_text(
        encoding="utf-8",
        errors="strict",
    )

    existing_symbols = extract_symbols(target_text)
    existing_names = {
        name
        for symbol in existing_symbols
        if (name := symbol_block_name(symbol))
    }

    source_symbols = extract_symbols(source_text)
    added_symbols = []
    added_names = set()
    skipped = 0

    for symbol in source_symbols:
        name = symbol_block_name(symbol)
        if not name:
            continue

        if name in existing_names or name in added_names:
            skipped += 1
            continue

        added_symbols.append(symbol)
        added_names.add(name)

    if not added_symbols:
        return len(existing_symbols), 0, skipped

    # Insert immediately before the library's final closing parenthesis.
    position = target_text.rstrip().rfind(")")
    if position == -1:
        raise RuntimeError(
            "Could not find end of destination symbol library."
        )

    suffix = target_text[position:]
    prefix = target_text[:position]

    if prefix and not prefix.endswith("\n"):
        prefix += "\n"

    insertion = ""
    for symbol in added_symbols:
        insertion += "\t" + symbol.strip() + "\n"

    target_path.write_text(
        prefix + insertion + suffix,
        encoding="utf-8",
    )

    return len(existing_symbols), len(added_symbols), skipped


def prepare_symbol_text(text, old_name, new_name, footprint_name):
    """Prepare a vendor symbol for production merging."""

    pattern = (
        r'(\(symbol\s+")'
        + re.escape(old_name)
        + r'(?P<tail>_[^"]*)?(")'
    )

    def replace_symbol(match):
        tail = match.group("tail") or ""
        return match.group(1) + new_name + tail + match.group(3)

    text, count = re.subn(pattern, replace_symbol, text)

    if count < 1:
        raise RuntimeError("Could not identify the symbol declaration.")

    if footprint_name:
        footprint_value = f"armadillo:{footprint_name}"

        text, count = re.subn(
            r'(\(property\s+"Footprint"\s+")[^"]*(")',
            lambda m: m.group(1) + footprint_value + m.group(2),
            text,
            count=1,
        )

        if count != 1:
            raise RuntimeError(
                "Could not identify the symbol Footprint property."
            )

        # Optional in vendor symbols; if present, keep it in step.
        text = re.sub(
            r'(\(property\s+"ki_fp_filters"\s+")[^"]*(")',
            lambda m: m.group(1) + footprint_name + m.group(2),
            text,
            count=1,
        )

    return text


def prepare_symbol_from_zip(zip_path, proposal):
    """Return prepared symbol text without touching production."""

    if (
        not proposal["symbol"]
        or proposal["use_existing_symbol"]
    ):
        return None
    
    with zipfile.ZipFile(zip_path, "r") as archive:
        symbol_text = archive.read(
            proposal["symbol"]["file"]
        ).decode("utf-8", errors="strict")

    return prepare_symbol_text(
        symbol_text,
        proposal["symbol"]["name"],
        proposal["symbol_name"],
        proposal["footprint_name"],
    )


def display_proposal(proposal):
    """Display proposed production changes."""

    print()
    print("PROPOSED ACTIONS")
    print("----------------")
    print()

    if proposal["symbol"]:

        print("Symbol:")

        if proposal["use_existing_symbol"]:
            print(
                f"  {proposal['symbol']['name']}"
                f" -> use existing "
                f"{proposal['symbol_library'].stem}:"
                f"{proposal['symbol_name']}"
            )
        else:
            print(
                f"  {proposal['symbol']['name']}"
                f" -> {proposal['symbol_name']}"
            )

        print(f"  Destination library: {proposal['symbol_library']}")

        if proposal["footprint"]:
            if proposal["use_existing_symbol"]:
                existing_footprint = get_symbol_footprint(
                    proposal["symbol_library"],
                    proposal["symbol_name"],
                )
                print(
                    "  Existing Footprint property:"
                    f" {existing_footprint or '(none)'}"
                )
                print("  Symbol will not be modified")
            else:
                print(
                    "  Footprint property:"
                    f" armadillo:{proposal['footprint_name']}"
                )
                print()

    else:
        print("Symbol:")
        print("  None")
        print()

    if proposal["footprint"]:

        source = Path(proposal["footprint"]["file"]).name

        destination = (
            FOOTPRINT_DIR
            / f"{proposal['footprint_name']}.kicad_mod"
        )

        print("Footprint:")
        print(f"  {source}")

        if proposal["use_existing_footprint"]:
            print(f"  -> use existing {destination}")
        else:
            print(f"  -> {destination}")

        print()
        
    else:
        print("Footprint:")
        print("  None")
        print()

    if proposal["model"]:

        source = Path(proposal["model"]).name
        destination = MODEL_DIR / source

        print("3D model:")
        print(f"  {source}")
        print(f"  -> {destination}")

        if proposal["link_model"]:
            print("  -> link to selected footprint")
        else:
            print("  -> no footprint link")

        print()

    else:
        print("3D model:")
        print("  None")
        print()

    print("No changes have been made yet.")

def destination_paths(proposal):
    """Return production destinations used by the proposal."""

    footprint_path = None
    model_path = None

    if proposal["footprint"]:
        footprint_path = (
            FOOTPRINT_DIR
            / f"{proposal['footprint_name']}.kicad_mod"
        )

    if proposal["model"]:
        model_path = (
            MODEL_DIR
            / Path(proposal["model"]).name
        )

    return footprint_path, model_path


def check_conflicts(zip_path, proposal):
    """Return a list of production files that already exist."""

    conflicts = []

    footprint_path, model_path = destination_paths(proposal)

    if (
        footprint_path
        and footprint_path.exists()
        and not proposal["use_existing_footprint"]
    ):
        conflicts.append(footprint_path)
        
    if model_path and model_path.exists():
        with zipfile.ZipFile(zip_path, "r") as archive:
            incoming_model = archive.read(proposal["model"])

        existing_model = model_path.read_bytes()

        if incoming_model != existing_model:
            conflicts.append(model_path)

    if (
        proposal["symbol"]
        and proposal["symbol_library"]
        and not proposal["use_existing_symbol"]
    ):
        if symbol_exists_in_library(
            proposal["symbol_library"],
            proposal["symbol_name"],
        ):
            conflicts.append(
                f"{proposal['symbol_library']} "
                f"(symbol {proposal['symbol_name']} already exists)"
            )

    return conflicts


def rename_footprint(text, old_name, new_name):
    """
    Synchronise the footprint's internal name and fp_text value.

    Only the first footprint declaration and first fp_text value are changed.
    """

    text, count = re.subn(
        r'\(footprint\s+(?:"[^"]+"|[^\s()]+)',
        lambda m: f'(footprint "{new_name}"',
        text,
        count=1,
    )

    if count != 1:
        raise RuntimeError(
            "Could not identify the footprint declaration."
        )

    text, count = re.subn(
        r'(\(fp_text\s+value\s+)(?:"[^"]*"|[^\s()]+)',
        lambda m: m.group(1) + new_name,
        text,
        count=1
    )

    if count != 1:
        raise RuntimeError(
            "Could not identify the footprint value field."
        )

    return text


def add_model_reference(text, model_filename):
    """Add a neutral KiCad 3D model reference to a footprint."""

    model_reference = (
        f"{MODEL_KICAD_PREFIX}/{model_filename}"
    )

    if "(model " in text:
        if f'(model "{model_reference}"' in text:
            return text

        raise RuntimeError(
            "Footprint already contains a different 3D model reference."
        )
    model_block = (
        f'  (model "{model_reference}"\n'
        f'    (offset (xyz 0 0 0))\n'
        f'    (scale (xyz 1 1 1))\n'
        f'    (rotate (xyz 0 0 0))\n'
        f'  )\n'
    )

    position = text.rfind(")")

    if position == -1:
        raise RuntimeError(
            "Could not find end of footprint."
        )

    return text[:position] + model_block + text[position:]


def make_symbol_backup(library_path):
    """Create and retain a timestamped symbol-library backup."""

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"{library_path.stem}_{stamp}.kicad_sym"

    counter = 1
    while backup.exists():
        backup = BACKUP_DIR / (
            f"{library_path.stem}_{stamp}_{counter}.kicad_sym"
        )
        counter += 1

    shutil.copy2(library_path, backup)
    return backup

def make_footprint_backup(footprint_path):
    """Create and retain a timestamped footprint backup."""

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / (
        f"{footprint_path.stem}_{stamp}.kicad_mod"
    )

    counter = 1
    while backup.exists():
        backup = BACKUP_DIR / (
            f"{footprint_path.stem}_{stamp}_{counter}.kicad_mod"
        )
        counter += 1

    shutil.copy2(footprint_path, backup)
    return backup


def perform_import(zip_path, proposal, prepared_symbol_text):
    """Promote the selected items with rollback on import failure."""

    footprint_path, model_path = destination_paths(proposal)

    FOOTPRINT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    created_paths = []
    symbol_backup = None
    footprint_backup = None
    symbol_library = proposal["symbol_library"]

    footprint_text = None
    model_data = None

    # Prepare everything from the ZIP before touching production.
    with zipfile.ZipFile(zip_path, "r") as archive:

        if proposal["footprint"]:

            if proposal["use_existing_footprint"]:
                footprint_text = footprint_path.read_text(
                    encoding="utf-8",
                    errors="strict",
                )

            else:
                source_name = proposal["footprint"]["file"]

                footprint_text = archive.read(source_name).decode(
                    "utf-8", errors="strict"
                )

                footprint_text = rename_footprint(
                    footprint_text,
                    proposal["footprint"]["name"],
                    proposal["footprint_name"],
                )

            if proposal["link_model"] and proposal["model"]:
                footprint_text = add_model_reference(
                    footprint_text,
                    Path(proposal["model"]).name,
                )
        if proposal["model"]:
            model_data = archive.read(proposal["model"])

    try:
        # Merge a new symbol first, protected by a retained backup.
        if proposal["symbol"] and not proposal["use_existing_symbol"]:
            symbol_backup = make_symbol_backup(symbol_library)

            existing, added, skipped = merge_symbol_text(
                prepared_symbol_text,
                symbol_library,
            )

            print()
            print(f"Existing in target: {existing}")
            print(f"Added: {added}   Skipped (dups): {skipped}")
            print(f"Output: {symbol_library}")

        if model_data is not None and not model_path.exists():
            with open(model_path, "xb") as output:
                output.write(model_data)
            created_paths.append(model_path)

        if footprint_text is not None:

            if proposal["use_existing_footprint"]:
                existing_text = footprint_path.read_text(
                    encoding="utf-8",
                    errors="strict",
                )

                if footprint_text != existing_text:
                    footprint_backup = make_footprint_backup(
                        footprint_path
                    )

                    footprint_path.write_text(
                        footprint_text,
                        encoding="utf-8",
                    )
            else:
                with open(
                    footprint_path, "x", encoding="utf-8"
                ) as output:
                    output.write(footprint_text)

                created_paths.append(footprint_path)
                
        archived_zip = archive_zip(zip_path)

        return symbol_backup, footprint_backup, archived_zip

    except Exception:
        for path in reversed(created_paths):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            
        if footprint_backup and footprint_backup.exists():
            shutil.copy2(
                footprint_backup,
                footprint_path
            )

        if symbol_backup and symbol_backup.exists():
            shutil.copy2(symbol_backup, symbol_library)

        raise


def archive_zip(zip_path):
    """Move a completed source ZIP into the archive."""

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination = ARCHIVE_DIR / zip_path.name

    if destination.exists():
        raise RuntimeError(
            f"Archive file already exists: {destination}"
        )

    shutil.move(str(zip_path), str(destination))
    return destination



def display_completed(
    proposal,
    symbol_backup=None,
    footprint_backup=None,
    archive_path=None,
):
    """Show what was actually installed."""

    footprint_path, model_path = destination_paths(proposal)

    print()
    print("IMPORT COMPLETE")
    print("---------------")
    print()

    if footprint_path:
        print(f"Footprint: {footprint_path}")

    if model_path:
        print(f"3D model:  {model_path}")

    if proposal["link_model"]:
        print("3D model reference present in footprint.")

    if proposal["symbol"]:
        print(f"Symbol:    {proposal['symbol_name']}")
        print(f"Library:   {proposal['symbol_library']}")

    if symbol_backup:
        print(f"Backup:    {symbol_backup}")

    if footprint_backup:
        print(f"Backup:    {footprint_backup}")

    if archive_path:
        print(f"Archived:  {archive_path}")

    print()



def inventory_zip(zip_path):
    """Return simple S/F/M presence flags for the ZIP selection list."""

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            symbols = False
            footprints = False
            models = False

            for member in archive.infolist():
                if member.is_dir():
                    continue

                category = classify_member(member.filename)

                if category == "symbol":
                    symbols = True
                elif category == "footprint":
                    footprints = True
                elif category == "model":
                    models = True

            return (
                "S" if symbols else "-",
                "F" if footprints else "-",
                "M" if models else "-",
            )

    except (zipfile.BadZipFile, OSError):
        return ("?", "?", "?")


def main():

    print()
    print("KiCad Component Import")
    print("----------------------")

    zip_files = find_zip_files()

    if not zip_files:
        print("\nNo ZIP files found in:")
        print(f"  {INCOMING_DIR}")
        return

    print("\nAvailable imports:\n")

    inventory = []

    for zip_path in zip_files:
        inventory.append(inventory_zip(zip_path))

    name_width = max(len(zip_path.name) for zip_path in zip_files)

    for number, (zip_path, flags) in enumerate(
        zip(zip_files, inventory), start=1
    ):
        s_flag, f_flag, m_flag = flags
        print(
            f"  {number}) {zip_path.name:<{name_width}}"
            f"   {s_flag}  {f_flag}  {m_flag}"
        )

    print()
    print("     S = symbol   F = footprint   M = 3D model")

    print()

    while True:

        choice = input("Select ZIP [1]: ").strip()

        if choice == "":
            choice = "1"

        try:
            selection = int(choice)

            if 1 <= selection <= len(zip_files):
                break

        except ValueError:
            pass

        print("Invalid selection.")

    selected_zip = zip_files[selection - 1]

    print()
    print(f"Inspecting: {selected_zip.name}")

    contents = inspect_zip(selected_zip)

    display_contents(contents)

    proposal = build_proposal(contents)

    display_proposal(proposal)

    archive_destination = ARCHIVE_DIR / selected_zip.name

    if archive_destination.exists():
        print()
        print("IMPORT STOPPED")
        print("--------------")
        print()
        print("Archive file already exists:")
        print(f"  {archive_destination}")
        print()
        print("Nothing has been changed.")
        return

    try:
        prepared_symbol_text = prepare_symbol_from_zip(
            selected_zip,
            proposal,
        )
    except Exception as error:
        print()
        print("IMPORT STOPPED")
        print("--------------")
        print()
        print(f"  {error}")
        print()
        print("Nothing has been changed.")
        return

    conflicts = check_conflicts(selected_zip, proposal)

    if conflicts:

        print()
        print("IMPORT STOPPED")
        print("--------------")
        print()
        print("The following production file(s) already exist:")
        print()

        for path in conflicts:
            print(f"  {path}")

        print()
        print("Nothing has been changed.")
        return


    print()
    print("This will now write the selected symbol, footprint")
    print("and/or 3D model to the production libraries.")
    print("On complete success the source ZIP will be archived.")
    print()

    if not ask_yes_no("Proceed?", default=False):
        print()
        print("Cancelled. Nothing has been changed.")
        return


    symbol_backup = None
    footprint_backup = None

    try:
        symbol_backup, footprint_backup, archived_zip = perform_import(
            selected_zip,
            proposal,
            prepared_symbol_text,
        )
        
    except Exception as error:

        print()
        print("IMPORT FAILED")
        print("-------------")
        print()
        print(f"  {error}")
        print()
        print(
            "If production changes had begun, the import "
            "transaction was rolled back."
        )
        return


    display_completed(
        proposal,
        symbol_backup=symbol_backup,
        footprint_backup=footprint_backup,
        archive_path=archived_zip,
    )
    
if __name__ == "__main__":
    main()

