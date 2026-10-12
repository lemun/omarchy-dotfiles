# Screensaver and lock-screen crash mitigation

On 2026-10-12, the local automatic display-switching helper was updated to
avoid changing monitor policy during locking and display sleep. The journal
showed monitor restore/disable cycles around Quickshell crashes, followed by
Omarchy's stranded-lock recovery. Several saved crash stacks passed through
GTK display handling; another passed through Qt DBus. The display-switching
guard is a mitigation for the observed loop, not a confirmed fix for every
underlying crash.

The screensaver starts before the automatic lock. If the lock client dies,
Hyprland can display its protective “lockscreen app died” drawing while apps
remain running behind it. Similar behavior is tracked in
[Omarchy issue 12208](https://github.com/omacom/omarchy/issues/12208).

## Preserve the guard when updating a monitor helper

Before a helper writes monitor toggles or calls `hyprctl reload`, inspect
`hyprctl -j monitors all`. Leave policy alone if an enabled output is asleep,
the compositor reports a lock, or the lock state cannot be determined.
Omarchy's compositor probe uses `solitaryBlockedBy`: `LOCK` indicates a lock;
`WORKSPACE` means that output could not reach the lock check. A missing field
must also be treated as unknown.

The installed helper puts this guard at the start of `reconcile(monitors)`,
after validating that `monitors` is a list:

```python
active = [m for m in monitors if m.get("disabled") is False]
if not active or any(
    "LOCK" in (m.get("solitaryBlockedBy") or [])
    or m.get("dpmsStatus") is False
    for m in active
):
    return
if not any(
    isinstance(m.get("solitaryBlockedBy"), list)
    and "WORKSPACE" not in m["solitaryBlockedBy"]
    for m in active
):
    return
```

Switching resumes on the next monitor event or periodic check after wake and
unlock. Omarchy's own emergency monitor recovery handles loss of an external
display while locked. Verify the lock indicators against the installed
Hyprland/Omarchy versions when porting or upgrading this helper.

## Current machine and applying an update

The hardware-specific source, updater and recovery script remain in
`~/Work/display-auto-switch`. That directory is local and is not a Git
repository. The installed source is
`~/.config/hypr/scripts/external-display-auto.py`; its user service is
`external-display-auto.service`.

After reviewing the source and approving the possible display changes, run:

```bash
bash ~/Work/display-auto-switch/update.sh
```

The updater asks for confirmation, saves a dated backup beside the installed
script, installs the source and restarts the helper. The restart may reconcile
active displays and move windows. The initial `install.sh` is for a fresh
installation and must not be used as an updater.

This repo preserves the reusable guard and instructions. It does not install
the hardware-specific monitor policy or copy active monitor toggles. On another
machine, adapt the local helper to its outputs and obtain approval before
applying display changes.

## Validation and recurrence

Isolated checks passed for locked, sleeping, unknown-lock, missing-indicator
and no-output states without policy changes or reloads. Awake connect and
disconnect still applied the expected policy. After the approved installation,
the source matched the staged helper, its service was active/running, and
Hyprland reported no configuration errors. Natural screensaver/lock use still
needs to establish whether the crashes recur; no lock or sleep test was run.

For a recurrence, record the approximate time and inspect the journal and
`coredumpctl` before restarting anything. Read-only checks include:

```bash
systemctl --user status external-display-auto.service
journalctl --user -u external-display-auto.service --since '30 minutes ago'
journalctl -b -t omarchy-shell --since '30 minutes ago'
coredumpctl list --since '30 minutes ago'
hyprctl configerrors
```

The local `recover-display.sh` stops the helper, removes its own disable toggle
and reloads Hyprland to restore the laptop panel. It changes displays and needs
explicit approval before an agent runs it. Restarting the shell, forcing a lock,
or testing display sleep likewise requires approval.
