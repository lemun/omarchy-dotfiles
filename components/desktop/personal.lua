-- Personal preferences, loaded after Omarchy defaults and local overrides.
-- Omarchy 4 Lua configuration; review before applying to a different version.
hl.config({
  input = {
    kb_layout = "us,il",
    kb_options = "compose:caps,shift:both_capslock_cancel,grp:alts_toggle",
    follow_mouse = 0,
  },
  general = { border_size = 2, gaps_in = 2, gaps_out = 2 },
  decoration = {
    rounding = 6,
    dim_inactive = true,
    dim_strength = 0.08,
    border_part_of_window = false,
    blur = { enabled = false },
    glow = { enabled = false },
  },
})
