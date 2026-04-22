#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-}"
OUTDIR="${2:-samples/in}"

if [[ -z "$INPUT" ]]; then
  echo "Uso: $0 <input-video> [output-dir]"
  exit 1
fi

mkdir -p "$OUTDIR"
ffmpeg -i "$INPUT" "$OUTDIR/frame_%05d.png"
