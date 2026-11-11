#!/usr/bin/env python3
"""Write a shell script that carries files inside it and runs a command on them.

Usage: pack.py OUTPUT COMMAND FILE...

The role runs this on the control node, then runs OUTPUT on a host with
ansible.builtin.script, which copies it over the connection without needing
Python on the host. That is how the role pushes package files or a Python
archive to a host that has no Python ansible-core can use yet. OUTPUT unpacks
each FILE into a temporary directory with base64, runs COMMAND in that
directory, and deletes it afterwards. The host needs only sh and base64.
"""

import base64
import os
import sys
import tempfile

MARKER = "__LIBRE_DEVOPS_PYTHON_PAYLOAD__"


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    output, command, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    names = [os.path.basename(f) for f in files]
    if len(set(names)) != len(names):
        print("pack.py: two files have the same name", file=sys.stderr)
        return 2

    directory = os.path.dirname(os.path.abspath(output))
    os.makedirs(directory, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=directory, prefix=".pack-")
    with os.fdopen(handle, "w", encoding="ascii") as script:
        script.write(
            "#!/bin/sh\n"
            "# Written by libre_devops.python (files/pack.py). Unpacks the files below into a\n"
            "# temporary directory, runs the command at the end there, and deletes the directory.\n"
            "set -eu\n"
            'PAYLOAD=$(mktemp -d)\n'
            "trap 'rm -rf \"$PAYLOAD\"' EXIT\n"
        )
        for path, name in zip(files, names):
            script.write(f"base64 -d > \"$PAYLOAD/{name}\" <<'{MARKER}'\n")
            with open(path, "rb") as source:
                while chunk := source.read(57 * 1024):
                    script.write(base64.encodebytes(chunk).decode("ascii"))
            script.write(f"{MARKER}\n")
        script.write('cd "$PAYLOAD"\n')
        script.write(command.rstrip("\n") + "\n")
    os.chmod(temporary, 0o644)
    os.replace(temporary, output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
