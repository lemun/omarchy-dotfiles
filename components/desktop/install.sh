#!/usr/bin/env bash
set -euo pipefail
[[ $EUID != 0 ]] || { echo 'Run as your normal user.' >&2; exit 1; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
config="$HOME/.config/hypr/hyprland.lua"
[[ -f $config ]] || { echo 'Requires Omarchy 4 Lua Hyprland config.' >&2; exit 1; }
echo 'This adds the saved US/Hebrew keyboard, focus and appearance preferences'
echo 'to Hyprland, which reloads on file changes. Windows may move as gaps change.'
read -r -p 'Approve this action? Type yes: ' answer
[[ $answer == yes ]] || exit 1
export DOTFILES_DESKTOP_SOURCE="$root"
python3 - <<'PY'
import os, shutil, tempfile
from pathlib import Path
source = Path(os.environ['DOTFILES_DESKTOP_SOURCE'])
config = Path.home() / '.config/hypr'
state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state')))
backups = state / 'omarchy-dotfiles/desktop-backups'
backups.mkdir(parents=True, exist_ok=True)
backup = Path(tempfile.mkdtemp(prefix='apply-', dir=backups))
for name in ('hyprland.lua', 'personal.lua'):
    target = config / name
    if target.is_symlink():
        raise SystemExit(f'Review symlink before installing: {target}')
    if target.exists():
        shutil.copy2(target, backup / name)
    else:
        (backup / (name + '.absent')).touch()
text = (config/'hyprland.lua').read_text()
line = 'require("hypr.personal")'
if line not in text.splitlines():
    text += '\n-- Personal preferences from omarchy-dotfiles.\n' + line + '\n'
# Install the module first so an automatic reload never sees a missing module.
shutil.copyfile(source/'personal.lua', config/'personal.lua')
(config/'hyprland.lua').write_text(text)
print(f'Backup: {backup}')
PY
hyprctl reload
errors=$(hyprctl configerrors)
if [[ -n $errors ]]; then
  printf 'Hyprland reported errors; restore the printed backup before continuing:\n%s\n' "$errors" >&2
  exit 1
fi
echo 'Desktop preferences applied. See docs/desktop.md for restore and optional touchpad settings.'
