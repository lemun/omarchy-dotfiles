# Optional desktop preferences

`./setup desktop` installs `~/.config/hypr/personal.lua` and appends its require
to your existing `hyprland.lua`. It keeps Omarchy's default loader and your
existing modules. It backs up both affected paths into a new directory under
`${XDG_STATE_HOME:-~/.local/state}/omarchy-dotfiles/desktop-backups/` on every run.
If personal.lua did not exist, the backup records `personal.lua.absent`.

The reviewed preferences are US/Hebrew layouts (Left Alt + Right Alt switches),
Caps Lock Compose, no mouse-driven focus, gaps of 2, a border of 2, rounding of
6, inactive dimming of 0.08, and disabled blur/glow. The final values come from
the active machine configuration, including its Omaland appearance overrides.
Other modules loaded later may override them. Existing settings not covered by
this module remain supplied by your local config and Omarchy defaults.

Hyprland applies config edits live. The installer asks for approval, reloads,
and checks `hyprctl configerrors`. If errors appear, use the printed backup to
restore; changing supported Hyprland versions can require editing this module.

To undo, choose the backup from before your first application. Restoring reloads
the live desktop, so announce the action and get approval before an agent runs it.
From a terminal, after selecting the actual backup path:

```bash
backup="$HOME/.local/state/omarchy-dotfiles/desktop-backups/REPLACE_WITH_BACKUP_DIRECTORY"
cp "$backup/hyprland.lua" "$HOME/.config/hypr/hyprland.lua"
if [ -f "$backup/personal.lua.absent" ]; then
  rm "$HOME/.config/hypr/personal.lua"
else
  cp "$backup/personal.lua" "$HOME/.config/hypr/personal.lua"
fi
hyprctl reload
hyprctl configerrors
```

The separate `macbook-touchpad.lua` records palm protection and disabled tap
click/drag. It is deliberately optional: review it for your hardware. To apply,
back up your config, copy it to `~/.config/hypr/macbook-touchpad.lua`, append
`require("hypr.macbook-touchpad")` to `hyprland.lua`, then reload and check errors
with approval. Physical clicks continue working. Undo by removing the require
and restoring the prior module/config backups.

Monitor IDs, scale, startup processes and suspend policies are not part of the
portable profile. Configure displays locally through Omarchy. Keybindings on the
inspected machine were stock examples; no binding overrides were exported.
