# Orca Matrix palette

The original `~/Work/orca-matrix-theme.py` used fixed Vite filenames, failed on
reruns, stored backups in a user directory and used `16 + JSON length` for the
ASAR data start. ASAR aligns the pickle header: the correct start is
`8 + header pickle size`. On the inspected Orca version the difference is one
byte. Its own verification repeated that offset error, so it missed invalid
hashes at the real asset boundaries.

The replacement discovers the main palette CSS in each renderer/web asset tree
by its variables. It accepts original or Matrix values and leaves unrelated
values (including light-theme declarations) alone. Every expected palette value
must be present. Unexpected layout, missing values, ambiguous assets, bad input
hashes or unsupported integrity metadata stop the operation before replacement.
Renamed Vite hashes work; arbitrary upstream palette/layout changes may require
a reviewed patch update.

The script keeps file lengths and ASAR offsets unchanged and edits only the
palette declarations and matching SHA256 metadata. It verifies whole CSS hashes
and every integrity block before patching, verifies staged output, replaces the
archive atomically, and verifies installed output and rerun behavior. A caught
post-replacement failure restores the input atomically. Backups and a recovery
receipt are persisted before replacement; abrupt process termination or a power
loss can require manual recovery. Existing file ownership and mode are preserved.

Installation copies the script to
`/usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py` (root:root, 0644).
The hook is `/etc/pacman.d/hooks/95-orca-matrix-theme.hook` (root:root, 0644).
It invokes `/usr/bin/python3 -I` with the installed script; isolated mode ignores
user Python paths and site packages. No checkout path is executed by the hook.
Root-only state lives at `/var/lib/orca-matrix-theme` (0700). All privileged
archive/state paths reject symlinks and non-root or writable ownership.

```bash
./setup orca
# Read only check (no sudo required):
/usr/bin/python3 -I /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py --check
# Explicit reapply, without launching or closing Orca:
sudo /usr/bin/python3 -I /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py --apply
sudo stat -c '%U:%G %a %n' /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py \
  /etc/pacman.d/hooks/95-orca-matrix-theme.hook /var/lib/orca-matrix-theme
```

Expected check status is `already-patched`; a stock supported archive reports
`compatible`. Apply on already patched files checks integrity and writes nothing.
Backups are named `<original-sha256>.asar`; each distinct stock archive has its
own backup. They are retained until you deliberately remove obsolete versions.
Allow roughly one additional archive's size per upgrade (currently about 125 MiB),
plus temporary space during replacement. `last-apply.json` records checksums,
assets and the most recent backup.

The Pacman Install/Upgrade Package trigger runs PostTransaction and depends on
Python. A failure is visible in Pacman's output, leaves unsupported archives
unchanged, and does not roll back the package transaction. After an upgrade,
check the installed palette. Do not repeatedly force substitutions after an
unsupported-version error. Update the reviewed palette/discovery code, then
rerun the installer to refresh the root-owned copy. `pacman -Qkk orca-ide-bin`
may report the deliberately modified app.asar; package removal/reinstallation
still belongs to Pacman.

## Restore and uninstall

Remove the hook first so future upgrades do not reapply the overlay:

```bash
sudo rm /etc/pacman.d/hooks/95-orca-matrix-theme.hook
sudo /usr/bin/python3 -I /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py --restore
# After successful restoration, optionally remove the installed script:
sudo rm /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py
```

Restore refuses unless the current archive matches the recorded patched digest
and the backup matches its original digest. It never restores an older package
archive over a new version. If the package changed, remove the hook and reinstall
`orca-ide-bin` through your AUR helper instead. Keep backups until recovery is
complete. Open Orca normally when ready; these commands do not close it.

## One-time recovery from the previous script

Use this only for an archive already modified by the old script. A regular
installer deliberately refuses its invalid CSS integrity. Review the saved
backup path; it must be the backup from before that old patch, for this version.
The script permits recovery only if the backup recreates the installed archive
byte for byte using the original algorithm. This is a migration, never something
the Pacman hook attempts automatically.

Run these commands in a terminal from this repository:

```bash
sudo install -d -o root -g root -m 0755 /usr/local/lib/omarchy-dotfiles
sudo install -d -o root -g root -m 0700 /var/lib/orca-matrix-theme
sudo install -o root -g root -m 0644 components/orca-matrix/orca-matrix-theme.py \
  /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py
# Substitute the backup path on the affected machine:
sudo install -o root -g root -m 0600 \
  "$HOME/.config/orca/app.asar.before-matrix-REPLACE_WITH_BACKUP_TIMESTAMP.bak" \
  /var/lib/orca-matrix-theme/legacy-original.asar
sudo /usr/bin/python3 -I /usr/local/lib/omarchy-dotfiles/orca-matrix-theme.py --repair-legacy
./setup orca
```

Recovery verifies the stock backup, retains both its content-addressed copy and
a `<sha256>.legacy-damaged.asar` copy of the old installed archive, then installs
the corrected palette and a receipt. `--restore` afterward restores the verified
stock archive. This recovery neither starts nor closes Orca.

References: [Electron ASAR implementation](https://github.com/electron/asar/blob/main/src/disk.ts)
and [Pacman hook format](https://man.archlinux.org/man/alpm-hooks.5.en).
