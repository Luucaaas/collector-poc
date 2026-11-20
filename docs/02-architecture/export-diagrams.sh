#!/usr/bin/env bash
# Exports the Mermaid diagrams of the architecture and quality documents as SVG.
#
# Single source: the ```mermaid blocks of the .md files in docs/02-architecture
# and docs/01-qualite.
# Each block to export contains a line "%% id: <name>", which gives the
# name of the file produced: img/<name>.svg, in the img/ folder next to the
# source .md. Blocks without an id are ignored.
#
# Usage: docs/02-architecture/export-diagrams.sh (from any folder)
# Prerequisites: Node.js >= 20 (mermaid-cli downloads a headless Chromium on
# first launch).

set -euo pipefail

MMDC_VERSION="11.17.0"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Folders containing .md files to export: the output goes to <folder>/img.
DOCS_DIRS=("$ROOT/docs/02-architecture" "$ROOT/docs/01-qualite")

count=0
for dir in "${DOCS_DIRS[@]}"; do
  mkdir -p "$dir/img" "$TMP/$(basename "$dir")"
  for md in "$dir"/*.md; do
    awk -v out="$TMP/$(basename "$dir")" '
      /^```mermaid/ { inblock = 1; name = ""; buf = ""; next }
      inblock && /^```/ {
        if (name != "") { f = out "/" name ".mmd"; printf "%s", buf > f; close(f) }
        inblock = 0; next
      }
      inblock {
        if (name == "" && match($0, /%% id: /)) { name = substr($0, RSTART + RLENGTH) }
        buf = buf $0 "\n"; next
      }
    ' "$md"
  done

  for src in "$TMP/$(basename "$dir")"/*.mmd; do
    [ -e "$src" ] || continue
    name="$(basename "$src" .mmd)"
    npx -y "@mermaid-js/mermaid-cli@${MMDC_VERSION}" \
      --input "$src" --output "$dir/img/${name}.svg" \
      --backgroundColor white --quiet
    echo "${dir#"$ROOT"/}/img/${name}.svg"
    count=$((count + 1))
  done
done

[ "$count" -gt 0 ] || { echo "No diagram with a \"%% id:\" line found." >&2; exit 1; }
echo "${count} diagram(s) exported."
