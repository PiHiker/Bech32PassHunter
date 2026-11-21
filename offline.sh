#!/bin/sh
# Run the CLI and its workers in a Linux network namespace with no uplink.
set -eu
umask 077
ulimit -c 0
if [ "$(uname -s)" != Linux ] || ! command -v unshare >/dev/null 2>&1; then
    echo "Network isolation requires Linux and util-linux unshare. Wallet tool not started." >&2
    exit 2
fi

project=$(CDPATH= cd -P -- "$(dirname -- "$0")" && pwd)
# Do not fall back to ordinary Python if the kernel denies namespace creation.
# Resolve the interpreter via PATH to respect the active virtual environment.
exec unshare --user --map-root-user --net -- python3 -I -B "$project/Bech32PassHunter.py" "$@"
