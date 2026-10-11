# Maintaining the setup and bar repositories

Keep both repositories:

| Repository | Responsibility |
|---|---|
| [omarchy-dotfiles](https://github.com/lemun/omarchy-dotfiles) | Setup entry point, Orca overlay, optional desktop preferences and recovery guides |
| [quickshell-dots](https://github.com/lemun/quickshell-dots) | Bar implementation, AirPods controls, saved shai profile, installer and bar updates |

The setup command uses the standalone fork. Deleting it from GitHub would break
new bar installations and updates. Replacing its main branch with upstream would
discard the personal customizations. Keeping it as a fork also preserves upstream
attribution and makes future merges straightforward.

## Save changes to the bar preferences

After changing the layout or appearance, run:

```bash
~/Work/quickshell-dots/scripts/qs-save-profile
```

This helper captures preferences, commits and pushes them to the fork. It needs a
clean main checkout and GitHub push access. See the fork's
[profile guide](https://github.com/lemun/quickshell-dots/blob/main/docs/airpods.md).
The setup repo does not contain a duplicate copy of that profile.

## Check for upstream bar updates

Fetching refs changes no running desktop processes:

```bash
git -C ~/Work/quickshell-dots fetch origin
git -C ~/Work/quickshell-dots fetch upstream
git -C ~/Work/quickshell-dots rev-list --left-right --count HEAD...origin/main
git -C ~/Work/quickshell-dots rev-list --left-right --count HEAD...upstream/main
```

The first number is commits unique to the checkout; the second is commits unique
to the remote. `0 0` for origin means the checkout is synchronized. A zero second
number for upstream means all upstream commits are already included; the first
number can be nonzero because it includes the fork's customization commits.

When upstream has new commits, merge them into your fork, resolve conflicts and
follow its [development checks](https://github.com/lemun/quickshell-dots/blob/main/docs/development.md)
before pushing. Its existing guide documents the merge commands. Do not use
GitHub's discard/reset option to overwrite the fork. Tests that stop/start the
bar or change the active desktop require explicit approval before an agent runs
them. Updating repository files alone does not require restarting the bar.

After publishing a reviewed bar change, use the existing bar update panel on each
machine when ready. The fork's deploy clone under `~/.local/share/quickshell-dots`
tracks `origin/main`; the updater stages and checks the new generation with its
backup and rollback behavior. Updates from the original project reach your
machines after you merge and publish them to your fork.

## Update this setup repo

```bash
git -C ~/Work/omarchy-dotfiles pull --ff-only origin main
```

Pulling alone does not apply components. Rerun `./setup orca` after patch changes
to refresh the root-owned script and hook. Apply desktop/bar/theme components
separately when ready; those commands announce effects and request approval.
After validating a component revision, update `components/versions.json` and
commit it here. The recorded revisions document reviewed versions; the external
installers follow their upstream branches.

At publication on 2026-10-11 the Quickshell checkout matched origin/main and
contained all upstream/main commits, plus five fork customization commits. No
upstream code merge was needed.
