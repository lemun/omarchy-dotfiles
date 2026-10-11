# Verification record

Completed 2026-10-11 against installed orca-ide-bin 1.4.217-1:

- Stock backup CSS full hashes and block hashes passed at the correct ASAR offsets.
- Applying the corrected palette produced the same-size archive with valid metadata.
- A second transform and a second installed apply returned a no-op.
- Renaming the Vite stylesheet hash names still discovered both palettes.
- Modified palette/input integrity data was rejected before archive replacement.
- The stock backup reproduced the old installed archive byte for byte using the
  previous script's algorithm, authorizing the narrow legacy repair.
- Live repair preserved the stock archive and legacy damaged archive, then verified
  the installed corrected archive and both CSS assets.
- Installed script and hook were root:root 0644; backup directory was root:root 0700.
- Setup and component installers passed Bash syntax checks.

Stock archive SHA256:
`03442cca51ff4edd0a6be276b638742a89962a830446ad8318ac3a198b6c7f91`

Corrected archive SHA256:
`433526a4719a98e9c8802b7bbaf5abaee0fd47987204ad03cb5b6f9188607f3b`

No package upgrade transaction was performed solely to exercise the hook. Its
Install/Upgrade trigger and root-owned Exec were checked against Pacman hook
documentation. No desktop/bar installation, compositor reload, application close,
reboot, suspend or power test was performed. Visual appearance is checked when
Orca is next opened normally. Another installation has not yet been exercised.

The previous `~/Work/orca-matrix-theme.py` now launches only the installed copy;
its original source is retained alongside it as
`orca-matrix-theme.py.before-dotfiles.bak`. Fresh installations use this repo.
