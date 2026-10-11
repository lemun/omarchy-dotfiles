#!/usr/bin/env bash
set -euo pipefail
[[ $EUID != 0 ]] || { echo 'Run as your normal user; only file installation uses sudo.' >&2; exit 1; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
command -v python3 >/dev/null
command -v sudo >/dev/null
# Check the package before enabling an automatic hook. Does not launch Orca.
if [[ -f /usr/lib/orca-ide/app.asar ]]; then
  /usr/bin/python3 -I "$root/orca-matrix-theme.py" --check
fi
# These are copies, never symlinks into the checkout. Root executes only the
# installed copy with isolated Python (ignores PYTHONPATH and user site packages).
sudo /usr/bin/install -d -o root -g root -m 0755 /usr/local/lib/omarchy-dotfiles
sudo /usr/bin/install -d -o root -g root -m 0700 /var/lib/orca-matrix-theme
sudo /usr/bin/install -o root -g root -m 0644 "$root/orca-matrix-theme.py" /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py
if [[ -f /usr/lib/orca-ide/app.asar ]]; then
  sudo /usr/bin/python3 -I /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py --apply
fi
sudo /usr/bin/install -d -o root -g root -m 0755 /etc/pacman.d/hooks
sudo /usr/bin/install -o root -g root -m 0644 "$root/95-orca-matrix-theme.hook" /etc/pacman.d/hooks/95-orca-matrix-theme.hook
echo 'Installed Orca patch and Pacman hook. Open Orca normally to see the palette.'
