#!/usr/bin/env bash
# Run the checked-in scene with a separately installed UrhoX desktop runtime.
set -eu
project=$(cd "$(dirname "$0")/.." && pwd)
runtime=$(command -v "${URHOX_RUNTIME:-UrhoXRuntime}") || {
    echo 'Set URHOX_RUNTIME to the path of the UrhoXRuntime executable.' >&2
    exit 1
}
cd "$(dirname "$runtime")"
exec "./$(basename "$runtime")" main.lua "-tapcode_dir=$project" -skip_login "$@"
