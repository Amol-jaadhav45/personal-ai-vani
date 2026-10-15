"""
gui/styles.py
==============
JARVIS-inspired design tokens — futuristic dark blue/cyan theme
with glowing accents and tech aesthetics.
"""

# ── Colour palette (Premium Titanium Space theme) ─────────────────────────
COLORS = {
    # Backgrounds — deep, rich dark grays (not just flat black)
    "bg_darkest":      "#09090b",       # Zinc 950
    "bg_dark":         "#18181b",       # Zinc 900 - panels, header
    "bg_panel":        "#27272a",       # Zinc 800 - sidebar, settings
    "bg_card":         "#3f3f46",       # Zinc 700 - cards
    "bg_input":        "#27272a",       # Zinc 800 - input field
    "bg_user":         "#0891b2",       # Cyan 600 - user chat bubble
    "bg_user_msg":     "#0891b2",       # Cyan 600 - user chat bubble
    "bg_assist_msg":   "#27272a",       # Zinc 800 - assistant chat bubble

    # Accent — Vibrant Cyan
    "accent":          "#06b6d4",       # Cyan 500
    "accent_hover":    "#22d3ee",       # Cyan 400
    "accent_glow":     "#06b6d4",       # glow effect color
    "accent_dim":      "#164e63",       # Cyan 900
    "accent_green":    "#10b981",       # Emerald 500
    "accent_red":      "#ef4444",       # Red 500
    "accent_yellow":   "#f59e0b",       # Amber 500
    "accent_orange":   "#f97316",       # Orange 500
    "accent_purple":   "#8b5cf6",       # Violet 500

    # Text
    "text_primary":    "#fafafa",       # Zinc 50
    "text_secondary":  "#a1a1aa",       # Zinc 400
    "text_muted":      "#52525b",       # Zinc 600
    "text_accent":     "#22d3ee",       # Cyan 400

    # Borders
    "border":          "#3f3f46",       # Zinc 700
    "border_focus":    "#06b6d4",       # Cyan 500
    "border_glow":     "#06b6d444",     # Semi-transparent cyan
}

# ── Typography ────────────────────────────────────────────────────────────────
FONTS = {
    "title":      ("Segoe UI", 24, "bold"),     # Clean, modern title
    "heading":    ("Segoe UI", 18, "bold"),
    "body":       ("Segoe UI", 14),
    "body_bold":  ("Segoe UI", 14, "bold"),
    "small":      ("Segoe UI", 12),
    "mono":       ("Consolas", 13),
    "mono_small": ("Consolas", 11),
    "hero":       ("Segoe UI Light", 32),       # Sleek hero text
}

# ── Sizing ────────────────────────────────────────────────────────────────────
SIZES = {
    "sidebar_w":       280,
    "input_height":    42,
    "corner_radius":   10,
    "msg_pad_x":       16,
    "msg_pad_y":       6,
    "window_min_w":    1100,
    "window_min_h":    700,
}
