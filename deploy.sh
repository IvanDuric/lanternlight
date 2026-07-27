#!/usr/bin/env bash
#
# Publish Lanternlight to github.com/IvanDuric/lanternlight, which GitHub Pages
# serves at https://ivanduric.github.io/lanternlight/
#
#   ./deploy.sh                        commit every change and push
#   ./deploy.sh "fixed the bulbs"      same, with your own commit message
#   ./deploy.sh --rebuild              re-export Episode 4 from Blender first
#   ./deploy.sh --rebuild "new press"  both
#
# Only what .gitignore allows is published (~22 MB). The Blender sources, print
# PDFs and raw footage stay on this Mac.

set -euo pipefail
cd "$(dirname "$0")"

REMOTE="https://github.com/IvanDuric/lanternlight.git"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
PAGES="https://ivanduric.github.io/lanternlight"

rebuild=0
message=""
for arg in "$@"; do
  case "$arg" in
    --rebuild) rebuild=1 ;;
    -*) echo "Unknown option: $arg" >&2; exit 1 ;;
    *) message="$arg" ;;
  esac
done
[ -z "$message" ] && message="Update $(date '+%Y-%m-%d %H:%M')"

# --- optional: rebuild Episode 4 from the .blend ------------------------------
if [ "$rebuild" = 1 ]; then
  if [ ! -x "$BLENDER" ]; then
    echo "Blender not found at $BLENDER" >&2; exit 1
  fi
  echo "==> Re-exporting Episode 4 from Scene4_Final.blend"
  "$BLENDER" --background Scene4_Final.blend --python animate_scene4_final.py
  echo "==> Shrinking textures"
  .venv/bin/python optimize_scene4_glb.py
fi

# --- make sure the remote is wired up -----------------------------------------
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "==> Adding remote origin -> $REMOTE"
  git remote add origin "$REMOTE"
fi
git branch -M main

# --- refuse to push anything GitHub will reject -------------------------------
# GitHub hard-rejects files over 100 MB. Catch it here rather than after a long
# upload. Nothing currently published is anywhere near this, but .gitignore only
# protects against the files we already know about.
oversize=$(git ls-files -z | xargs -0 -I{} sh -c \
  'size=$(stat -f%z "{}" 2>/dev/null || stat -c%s "{}"); [ "$size" -gt 94371840 ] && echo "  {} ($((size/1048576)) MB)"' || true)
if [ -n "$oversize" ]; then
  echo "Refusing to push — these exceed GitHub's 100 MB limit:" >&2
  echo "$oversize" >&2
  echo "Add them to .gitignore, then run again." >&2
  exit 1
fi

# --- commit -------------------------------------------------------------------
git add -A
if git diff --cached --quiet; then
  echo "==> Nothing changed since the last deploy"
else
  git commit -q -m "$message"
  echo "==> Committed: $message"
  git show --stat --oneline HEAD | tail -n +2 | sed 's/^/    /'
fi

# --- push ---------------------------------------------------------------------
echo "==> Pushing to $REMOTE"
git push -u origin main

published=$(git ls-files | wc -l | tr -d ' ')
echo
echo "==> Pushed $published files. Live in a minute or two:"
echo "      $PAGES/            character menu"
echo "      $PAGES/ep/04/      Episode 4 — Silva and the press"
