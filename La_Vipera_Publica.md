# La Vipera Publica

## Design Principles

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
