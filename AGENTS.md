Use the omarchy skill for user configuration changes. Never edit packaged Omarchy files.
Keep quickshell-dots standalone; delegate to its installer and guide.
Never run checkout code automatically as root. Pacman uses a root-owned installed copy
of the Orca script with isolated Python. Refresh that copy explicitly after edits.
Before anything that could interrupt the active session, announce the exact action
and likely effect and get explicit user approval. This includes changing/restarting
the bar, display changes, suspend, hibernate, reboot, shutdown, and power tests.
Do not configure automatic shutdown on lid close on the user's MacBookPro14,2.
Never copy credentials, pairing keys, runtime caches, or machine identifiers.

Treat requested Omarchy tweaks and ricing as portable dotfiles changes by default.
Persist them in this repo or the appropriate standalone fork, update restoration
instructions, and commit and push validated changes unless the user requests local
only work. Save exact Quickshell preferences in quickshell-dots/profiles/shai;
this repo's setup quickshell command restores that profile. Preserve the rule
against copying secrets, runtime data, and machine-specific configuration.
