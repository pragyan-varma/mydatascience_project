"""Shared display constants for the dashboard UI.

Team colors are national-team identity colors (an entity carries its own color),
used for the split win-probability bars and cards. Any team not listed falls back
to a neutral slate so the UI never breaks on an unmapped name.
"""

FALLBACK_COLOR = "#64748b"  # neutral slate

TEAM_COLORS = {
    "Argentina": "#6cace4",
    "Brazil": "#f7c331",
    "France": "#1e3a8a",
    "Spain": "#c60b1e",
    "England": "#cf1020",
    "Portugal": "#006600",
    "Germany": "#111111",
    "Netherlands": "#f36c21",
    "Belgium": "#c8102e",
    "Croatia": "#c81e3c",
    "Uruguay": "#5b9bd5",
    "Colombia": "#fcd116",
    "Mexico": "#006847",
    "United States": "#3c3b6e",
    "Canada": "#d52b1e",
    "Morocco": "#c1272d",
    "Senegal": "#00853f",
    "Japan": "#bc002d",
    "South Korea": "#0047a0",
    "Switzerland": "#d52b1e",
    "Austria": "#ed2939",
    "Australia": "#00843d",
    "Ecuador": "#ffd100",
    "Norway": "#ba0c2f",
    "Sweden": "#006aa7",
    "Denmark": "#c8102e",
    "Poland": "#dc143c",
    "Ghana": "#006b3f",
    "Ivory Coast": "#f77f00",
    "Egypt": "#c8102e",
    "Nigeria": "#008751",
    "Tunisia": "#e70013",
    "Algeria": "#006233",
    "Cape Verde": "#003893",
    "DR Congo": "#007fff",
    "South Africa": "#007749",
    "Iran": "#239f40",
    "Saudi Arabia": "#006c35",
    "Qatar": "#8a1538",
    "Iraq": "#007a3d",
    "Jordan": "#007a3d",
    "Uzbekistan": "#1eb53a",
    "Paraguay": "#d52b1e",
    "Panama": "#005293",
    "Haiti": "#00209f",
    "Curaçao": "#002b7f",
    "Scotland": "#0065bd",
    "Turkey": "#e30a17",
    "Czech Republic": "#11457e",
    "New Zealand": "#00247d",
    "Bosnia and Herzegovina": "#002395",
}


FALLBACK_SECONDARY = "#94a3b8"

TEAM_SECONDARY = {
    "Argentina": "#f2f4f7", "Brazil": "#009739", "France": "#ED2939", "Spain": "#FFC400",
    "England": "#e5e7eb", "Portugal": "#DA020E", "Germany": "#DD0000", "Netherlands": "#21468B",
    "Belgium": "#FDDA24", "Croatia": "#0093DD", "Uruguay": "#FCD116", "Colombia": "#003893",
    "Mexico": "#CE1126", "United States": "#B22234", "Canada": "#e5e7eb", "Morocco": "#006233",
    "Senegal": "#FDEF42", "Japan": "#e5e7eb", "South Korea": "#C60C30", "Switzerland": "#e5e7eb",
    "Austria": "#e5e7eb", "Australia": "#FFCD00", "Ecuador": "#034EA2", "Norway": "#00205B",
    "Sweden": "#FECC02", "Ghana": "#CE1126", "Ivory Coast": "#009e60", "Egypt": "#3a3a3a",
    "Tunisia": "#e5e7eb", "Algeria": "#D21034", "Cape Verde": "#CF2027", "DR Congo": "#F7D618",
    "South Africa": "#FFB915", "Iran": "#DA0000", "Saudi Arabia": "#e5e7eb", "Qatar": "#e5e7eb",
    "Iraq": "#CE1126", "Jordan": "#CE1126", "Uzbekistan": "#0099B5", "Paraguay": "#0038A8",
    "Panama": "#D21034", "Haiti": "#D21034", "Curaçao": "#F9D90F", "Scotland": "#e5e7eb",
    "Turkey": "#e5e7eb", "Czech Republic": "#D7141A", "New Zealand": "#CC142B",
    "Bosnia and Herzegovina": "#FECB00",
}

TEAM_FLAGS = {
    "Argentina": "🇦🇷", "Brazil": "🇧🇷", "France": "🇫🇷", "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Portugal": "🇵🇹", "Germany": "🇩🇪", "Netherlands": "🇳🇱", "Belgium": "🇧🇪", "Croatia": "🇭🇷",
    "Uruguay": "🇺🇾", "Colombia": "🇨🇴", "Mexico": "🇲🇽", "United States": "🇺🇸", "Canada": "🇨🇦",
    "Morocco": "🇲🇦", "Senegal": "🇸🇳", "Japan": "🇯🇵", "South Korea": "🇰🇷", "Switzerland": "🇨🇭",
    "Austria": "🇦🇹", "Australia": "🇦🇺", "Ecuador": "🇪🇨", "Norway": "🇳🇴", "Sweden": "🇸🇪",
    "Ghana": "🇬🇭", "Ivory Coast": "🇨🇮", "Egypt": "🇪🇬", "Tunisia": "🇹🇳", "Algeria": "🇩🇿",
    "Cape Verde": "🇨🇻", "DR Congo": "🇨🇩", "South Africa": "🇿🇦", "Iran": "🇮🇷", "Saudi Arabia": "🇸🇦",
    "Qatar": "🇶🇦", "Iraq": "🇮🇶", "Jordan": "🇯🇴", "Uzbekistan": "🇺🇿", "Paraguay": "🇵🇾",
    "Panama": "🇵🇦", "Haiti": "🇭🇹", "Curaçao": "🇨🇼", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Turkey": "🇹🇷",
    "Czech Republic": "🇨🇿", "New Zealand": "🇳🇿", "Bosnia and Herzegovina": "🇧🇦",
}


def team_color(team: str) -> str:
    return TEAM_COLORS.get(team, FALLBACK_COLOR)


def team_secondary(team: str) -> str:
    return TEAM_SECONDARY.get(team, FALLBACK_SECONDARY)


def team_flag(team: str) -> str:
    return TEAM_FLAGS.get(team, "⚽")


def team_gradient(team: str) -> str:
    """CSS linear-gradient string from a team's primary → secondary colors."""
    return f"linear-gradient(135deg, {team_color(team)} 0%, {team_secondary(team)} 100%)"
