#!/usr/bin/env bash
# Exporte en SVG les diagrammes Mermaid des documents d'architecture et de qualité.
#
# Source unique : les blocs ```mermaid des fichiers .md de docs/02-architecture
# et de docs/01-qualite.
# Chaque bloc à exporter contient une ligne « %% id: <nom> », qui donne le
# nom du fichier produit : img/<nom>.svg, dans le dossier img/ voisin du .md
# source. Les blocs sans id sont ignorés.
#
# Usage : docs/02-architecture/export-diagrams.sh (depuis n'importe quel dossier)
# Prérequis : Node.js >= 20 (mermaid-cli télécharge un Chromium headless au
# premier lancement).

set -euo pipefail

MMDC_VERSION="11.17.0"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Dossiers contenant des .md à exporter : la sortie va dans <dossier>/img.
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

[ "$count" -gt 0 ] || { echo "Aucun diagramme avec « %% id: » trouvé." >&2; exit 1; }
echo "${count} diagramme(s) exporté(s)."
