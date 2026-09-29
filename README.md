# La Vipera Publica

La Vipera Publica is a small Linux utility for importing vendor-supplied
KiCad component ZIP files.

It can import:

-   KiCad symbols
-   KiCad footprints
-   STEP 3D models

It is currently tested on:

-   Ubuntu 22.04 LTS and 24.04 LTS
-   KiCad 9 and KiCad 10

## Installation

Before installing La Vipera, install KiCad and complete KiCad's normal
first-use setup. This allows KiCad to create its user library tables.

1.  Download `la-vipera.zip`.

2.  Extract the ZIP.

3.  Open a terminal in the extracted `la-vipera` directory.

4.  Run:

        python3 install.py

5.  When installation finishes, run:

        source ~/.profile

6.  Start La Vipera:

        la-vipera

The installer creates:

    ~/La_Vipera

La Vipera creates its own KiCad symbol and footprint libraries and
registers them with KiCad automatically the first time it runs.

If La Vipera is installed or run before KiCad has completed its
first-use setup, installation will still succeed. Library registration
will be skipped until KiCad has created its user library tables. Run La
Vipera again after completing KiCad's normal first-use setup.

## Using La Vipera

1.  Download a KiCad component ZIP from your component supplier.

2.  Copy the ZIP, unchanged, into:

        ~/La_Vipera/workspace/incoming

3.  Run:

        la-vipera

4.  La Vipera will inspect the ZIP and show the components it has found.

5.  Follow the prompts to select the destination libraries and confirm
    the import.

6.  After a successful import, the original ZIP is moved to:

        ~/La_Vipera/workspace/archive

Backups of modified libraries are stored in:

    ~/La_Vipera/workspace/backups

Files that cannot currently be processed can be kept in:

    ~/La_Vipera/workspace/quarantine

## Libraries

La Vipera provides its own default libraries:

    ~/La_Vipera/libraries/La_Vipera.kicad_sym
    ~/La_Vipera/libraries/La_Vipera.pretty
    ~/La_Vipera/libraries/La_Vipera.3dshapes

It also discovers suitable user-defined KiCad symbol and footprint
libraries and allows them to be selected as import destinations.

La Vipera does not modify the standard KiCad libraries.

## Problems and Testing

La Vipera Publica is new software and wider testing is welcome.

If you find a vendor ZIP that La Vipera cannot process, please report it
on the GitHub project together with the supplier and component details.

Please do not disturb the snake.
