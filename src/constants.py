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


def team_color(team: str) -> str:
    return TEAM_COLORS.get(team, FALLBACK_COLOR)
