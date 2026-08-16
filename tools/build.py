#!/usr/bin/env python3
"""Assemble the distributed MAS scripts from the sources in MAS/src.

Every script in MAS/All-In-One-Version-KL and MAS/Separate-Files-Version is
generated from a matching ``*.cmd.in`` template under MAS/src. A template is a
verbatim copy of the script except that the code shared with other scripts is
replaced by include directives:

    ::@include lib/common/dk_setvar.cmdinc

The directive is replaced by the contents of the referenced file, so editing a
shared subroutine once updates every script that uses it.

Usage:
    python tools/build.py            # write the generated scripts
    python tools/build.py --check    # fail if the generated scripts are stale
"""

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "MAS" / "src"
OUT = REPO / "MAS"
ENCODING = "cp1252"
EOL = "\r\n"
INCLUDE = re.compile(r"^::@include (\S+)\s*$")


def read(path: Path) -> str:
    return path.read_bytes().decode(ENCODING)


def expand(template: Path, stack=()) -> str:
    """Return the text of ``template`` with all include directives expanded."""
    if template in stack:
        chain = " -> ".join(str(p.relative_to(SRC)) for p in (*stack, template))
        raise SystemExit(f"ERROR: circular include: {chain}")
    lines = []
    for lineno, line in enumerate(read(template).split(EOL), 1):
        match = INCLUDE.match(line)
        if not match:
            lines.append(line)
            continue
        include = SRC / match.group(1)
        if not include.is_file():
            rel = template.relative_to(SRC)
            raise SystemExit(f"ERROR: {rel}:{lineno}: missing include {match.group(1)}")
        text = expand(include, (*stack, template))
        # Includes are stored with a trailing newline; the directive line itself
        # does not carry one, so drop it before splicing the text in.
        lines.append(text[: -len(EOL)] if text.endswith(EOL) else text)
    return EOL.join(lines)


def targets():
    for template in sorted(SRC.rglob("*.cmd.in")):
        yield template, OUT / template.relative_to(SRC).with_suffix("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed scripts match the sources instead of writing them",
    )
    args = parser.parse_args()

    stale = []
    for template, output in targets():
        text = expand(template).encode(ENCODING)
        rel = output.relative_to(REPO).as_posix()
        if args.check:
            if not output.is_file() or output.read_bytes() != text:
                stale.append(rel)
            continue
        if output.is_file() and output.read_bytes() == text:
            print(f"unchanged {rel}")
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(text)
        print(f"wrote     {rel}")

    if stale:
        print("ERROR: these scripts do not match MAS/src, run tools/build.py:")
        for rel in stale:
            print(f"  {rel}")
        return 1
    if args.check:
        print("All scripts match MAS/src.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
