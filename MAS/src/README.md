# MAS sources

The scripts shipped in `MAS/All-In-One-Version-KL` and `MAS/Separate-Files-Version`
are single-file by design: each one has to run on its own after being downloaded
or piped into PowerShell. That is why the same environment bootstrap and the same
`:dk_*` helper routines were copy-pasted into all of them.

This directory keeps a single copy of that shared code, so a fix has to be made
once instead of once per script.

```
src/
  lib/                     shared fragments (*.cmdinc)
    common/                environment bootstrap and the :dk_* helpers
    kms/ office/ ohook/    routines shared by the feature-specific scripts
    tsforge/ windows/
    misc/                  everything else shared by two or more scripts
  All-In-One-Version-KL/MAS_AIO.cmd.in
  Separate-Files-Version/...cmd.in
```

A `*.cmd.in` template is the script itself, with each shared block replaced by an
include directive:

```
::@include lib/common/dk_setvar.cmdinc
```

Includes may nest, and a directive expands to the file contents verbatim, so the
generated script is plain batch with no runtime dependency on this directory.
When two scripts carry genuinely different versions of the same routine, the
minority version stays inline or lives in a `_v2` fragment; nothing is merged
behind a flag.

## Building

```
python tools/build.py            # regenerate the shipped scripts
python tools/build.py --check    # fail if the shipped scripts are out of date
```

The shipped scripts stay committed, so users keep downloading a single file and
`--check` (run in CI) guarantees they are byte-for-byte what the sources produce.

## Workflow

1. Edit the fragment in `lib/` or the relevant `*.cmd.in`.
2. Run `python tools/build.py`.
3. Commit the sources and the regenerated scripts together.

Never edit `MAS/**/*.cmd` directly: the next build overwrites it.
