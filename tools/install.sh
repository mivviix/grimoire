#!/bin/sh
# Symlink the commands and the skill out of this repo (source stays here).
set -e
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.local/bin ~/.claude/skills
ln -sfn "$here/grim.py" ~/.local/bin/grim
ln -sfn "$here/inscribe.py" ~/.local/bin/inscribe
ln -sfn "$here/skill" ~/.claude/skills/grimoire
echo "installed: grim, inscribe, skill grimoire"
