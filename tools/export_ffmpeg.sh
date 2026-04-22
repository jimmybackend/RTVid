#!/usr/bin/env bash
set -euo pipefail

INDIR="${1:-samples/out}"
OUTPUT="${2:-export.mp4}"
FPS="${3:-25}"

ffmpeg -framerate "$FPS" -i "$INDIR/frame_%05d.png" -pix_fmt yuv420p "$OUTPUT"
