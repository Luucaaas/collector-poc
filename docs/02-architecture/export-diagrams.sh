#!/usr/bin/env bash
# Exporte en SVG les diagrammes Mermaid des documents d'architecture.
#
# Source unique : les blocs ```mermaid des fichiers .md de ce dossier.
# Chaque bloc à exporter contient une ligne « %% id: <nom> », qui donne le
# nom du fichier produit : img/<nom>.svg. Les blocs sans id sont ignorés.
#
# Usage : docs/02-architecture/export-diagrams.sh
# Prérequis : Node.js >= 20 (mermaid-cli télécharge un Chromium headless au
# premier lancement).

set -euo pipefail

MMDC_VERSION="11.17.0"
DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$DIR/img"

for md in "$DIR"/*.md; do
  awk -v out="$TMP" '
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

count=0
for src in "$TMP"/*.mmd; do
  [ -e "$src" ] || { echo "Aucun diagramme avec « %% id: » trouvé." >&2; exit 1; }
  name="$(basename "$src" .mmd)"
  npx -y "@mermaid-js/mermaid-cli@${MMDC_VERSION}" \
    --input "$src" --output "$DIR/img/${name}.svg" \
    --backgroundColor white --quiet
  echo "img/${name}.svg"
  count=$((count + 1))
done

echo "${count} diagramme(s) exporté(s) dans $DIR/img/"
