# Inventory and portability decisions

Inspected 2026-10-11 on Omarchy 4.0.4-1, MacBookPro14,2. This is a curated record,
not a dump of local state.

| Existing customization | Where it belongs |
|---|---|
| Quickshell Rise V2, AirPods UI and shai profile | Standalone lemun/quickshell-dots; linked by setup |
| Matrix desktop theme | BVisagie/omarchy-matrix-theme, installed through Omarchy |
| Matrix Orca palette | This repo's independent package overlay |
| US/Hebrew keyboard and appearance | Optional components/desktop/personal.lua |
| MacBook touchpad palm protection | Optional components/desktop/macbook-touchpad.lua |
| AirPods plugin/librepods daemon | Independent omarchy-pods setup; pair devices locally |
| DP-2/eDP-1 automatic display switching | Existing ~/Work/display-auto-switch, hardware specific |
| Omaland and omazed theme hook | Local optional tools; install separately if desired |

`~/Work/display-auto-switch` has its own scripts and README but is not a Git
repository. It uses DP-2/eDP-1 and changes live displays, so the new entry point
does not execute it. On another machine, port its monitor assumptions first,
review its recovery commands, announce the display action and obtain approval
before installing. Do not copy its active monitor-disable toggles.

The helper received a lock/display-sleep guard on 2026-10-12 after repeated
Quickshell lock-screen crashes around monitor switching. The reusable guard,
update instructions, validation and recovery notes are preserved in
[Display and lock-screen crashes](display-lock-crashes.md). The installed
mitigation still needs confirmation through normal idle use.

The inspected Hyprland startup loads an external-display-auto user service; this
is tied to that display component. The existing monitor config uses preferred
modes and scale 1. Neither is exported as a universal monitor policy.

The existing stock shell configuration has a left bar, local plugins and idle
preferences. Quickshell already owns its saved layout and startup/theme hooks;
copying shell.json would conflate those systems and overwrite unrelated local
preferences. Keep the fork's installer responsible for its integration. Account
usage caches, shell runtime data, plugin caches, pairing keys and credentials
were not copied. Local installed hooks (including omazed) are inventoried rather
than silently executed or exported.

Battery drain and heat during sleep require a separate hardware investigation.
This repo does not configure power management or lid actions. Automatic shutdown
on lid close is ruled out for this MacBook. Any suspend, hibernate, reboot,
shutdown, or power-management test requires exact-effect announcement and the
user's explicit reply before execution, including tests called dry runs.
