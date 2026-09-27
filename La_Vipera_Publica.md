# La Vipera Publica

## Design Principles

### Design Decision Documentation

Where a design choice requires consideration between reasonable alternatives,
the decision and its rationale should be recorded in this document.

The purpose is not to document every implementation detail, but to preserve
the reasoning behind choices that a future user, maintainer or contributor
might reasonably question.

A useful test is:

> If we had to stop and think about it, somebody may eventually ask why we did it.

### Platform Support

La Vipera Publica is initially intended to support Ubuntu 22.04 LTS and
Ubuntu 24.04 LTS.

Development should avoid unnecessary distribution-specific behaviour so that
La Vipera may also operate on other Linux distributions. However, operation
on an untested distribution does not imply that the distribution is formally
supported.

A distinction is made between:

- **Supported platforms** — platforms on which La Vipera is deliberately
  tested and maintained.
- **Reported compatible platforms** — platforms on which users have reported
  successful operation but which are not part of the maintained test set.

User reports of successful operation on other distributions are welcome and
may be documented as reported compatibility.

The bootstrap installer should require only Python 3 and its standard library.
Its minimum Python version must be no newer than that provided by the oldest
supported Ubuntu release unless there is a compelling reason otherwise.

### Workspace Ownership

La Vipera must not assume that an existing `~/La_Vipera` directory belongs
to it merely because the directory name matches its default workspace name.

A workspace created by La Vipera will contain an identifying marker:

    ~/La_Vipera/.la_vipera

If `~/La_Vipera` does not exist, the installer may create it and its ownership
marker.

If `~/La_Vipera` exists and contains a valid identifying marker, the installer
may treat it as an existing La Vipera workspace. Existing files and directories
must still be preserved.

If `~/La_Vipera` exists without a valid identifying marker, the installer must stop
without modifying the directory. The user must decide how the naming conflict
is to be resolved.

La Vipera must not automatically rename, replace, delete or adopt an
unidentified existing directory.

**Principle:** a matching pathname is not proof of ownership.

### 1. Library Ownership and Configuration

**La Vipera owns its workspace; it references the user's libraries.**

La Vipera will create and manage its own working environment, including:

- incoming packages
- archived packages
- backups
- configuration
- default symbol, footprint and 3D-model libraries

Existing user libraries remain under the user's control and will not be moved,
renamed or reorganised merely to suit La Vipera.

On first run, La Vipera should discover existing KiCad libraries where practical
and allow the user to select which libraries are to be used as import
destinations. These selections are stored as configuration paths.

La Vipera will also provide valid default libraries of its own:

- `La_Vipera.kicad_sym`
- `La_Vipera.pretty`
- `La_Vipera.3dshapes`

These may remain empty when the user chooses existing libraries, but provide:

- an immediately usable environment for a new installation;
- a safe destination for testing uncertain vendor packages;
- a known-good fallback if an existing library is unavailable or unsuitable;
- a recovery path following configuration errors or other misadventures.

The default La Vipera libraries are permanent, ordinary KiCad libraries rather
than temporary staging areas.

**Principle:** discovery does not imply modification. La Vipera should adapt to
the user's existing KiCad environment rather than require that environment to
be reorganised around La Vipera.

### 2. Filesystem Layout

La Vipera separates user-visible working data from application configuration
and installed program files.

The default user workspace is:

    ~/La_Vipera/
    ├── workspace/
    │   ├── incoming/
    │   ├── archive/
    │   └── backups/
    └── libraries/
        ├── La_Vipera.kicad_sym
        ├── La_Vipera.pretty/
        └── La_Vipera.3dshapes/

Application configuration is stored separately:

    ~/.config/la-vipera/

The installed executable will reside in:

    ~/.local/bin/

The `libraries` directory contains genuine KiCad libraries that the user may
wish to inspect, edit, back up or configure directly in KiCad. They are
therefore deliberately kept in a visible location under the user's home
directory rather than hidden beneath `~/.local/share`.

The `workspace` directory contains La Vipera's operational material. Keeping
it separate from `libraries` makes the distinction between permanent KiCad
assets and La Vipera's housekeeping explicit.

Configuration and executable files follow normal Linux per-user conventions
because users do not ordinarily need to manipulate them directly.

No existing user libraries are moved or reorganised by this layout.

### 3. Release Packaging and Distribution

Public releases of La Vipera should be distributed as deliberately prepared
release archives rather than relying solely on GitHub's automatically generated
source-code archives.

A release ZIP should contain only the files required by an ordinary user to
understand and install La Vipera, such as:

- the installer;
- the application;
- documentation;
- licence information;
- icons or other required application resources.

Development files and other repository material that are not useful to an
ordinary user need not be included.

The intended installation process should not require the user to understand
Git or clone a repository. A typical user should be able to download the
release ZIP, extract it and run the supplied installer.

During development and testing, cloning the Git repository remains appropriate
because it provides a convenient way to obtain and update development versions.

The installer should normally install the application supplied within the
release package rather than downloading additional application files from
GitHub. This keeps the release package self-contained and makes its contents
explicit and testable.

**Principle:** we should know exactly what we are shipping.


### 4. Open-Source Collaboration

La Vipera Publica is intended to be an open-source project. Users should not
be required to register merely to download or use the software.

The project should instead encourage users and developers to establish a
relationship with the project through the normal collaborative mechanisms
provided by GitHub.

Contributions may include:

- bug reports and fixes;
- support for additional vendor package formats;
- improvements to existing functionality;
- reports of successful operation with other Linux distributions or KiCad
  versions;
- documentation improvements;
- proposed new features.

Significant improvements are particularly encouraged to be contributed back
to the project through issues, discussions or pull requests where practical.

It is accepted that an open-source user may modify La Vipera privately without
reporting or contributing those changes. The project should encourage
collaboration rather than attempt to enforce it through download registration
or other barriers.

A permissive open-source licence is preferred so that users are free to study,
use and improve La Vipera. The specific licence will be selected before the
first public release.

**Principle:** make contribution easy and welcome rather than making
participation compulsory.
