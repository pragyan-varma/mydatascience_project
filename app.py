import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from constants import team_color  # noqa: E402
from history import wc_goals_by_year, wc_history  # noqa: E402
from predictor import (  # noqa: E402
    get_recent_form,
    get_team_rating,
    list_teams,
    predict_match,
)
from simulator import run_monte_carlo  # noqa: E402

st.set_page_config(page_title="World Cup 2026 Analytics", page_icon="⚽", layout="wide")

# ---------------------------------------------------------------- styling (Apple-inspired)
APPLE_FONT = '"SF Pro Display","SF Pro Text",-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif'
INK = "#1d1d1f"
SUBTLE = "#86868b"
ACCENT = "#0071e3"
TILE = "#f5f5f7"

st.markdown(
    f"""
    <style>
      html, body, .stApp, [class*="css"], button, input, select, textarea {{
        font-family: {APPLE_FONT} !important;
        -webkit-font-smoothing: antialiased;
      }}
      .stApp {{ background: #ffffff; }}
      .block-container {{ max-width: 1040px; padding-top: 1.5rem; }}

      .hero {{ text-align: center; padding: 54px 20px 34px; }}
      .hero h1 {{ margin: 0; font-size: 3.1rem; font-weight: 600; letter-spacing: -.02em;
        color: {INK}; line-height: 1.06; }}
      .hero p {{ margin: 16px auto 0; max-width: 620px; font-size: 1.2rem; font-weight: 400;
        color: {SUBTLE}; line-height: 1.45; }}

      h2, h3 {{ color: {INK} !important; font-weight: 600 !important; letter-spacing: -.01em; }}

      .card {{ background: {TILE}; border-radius: 18px; padding: 22px 24px; height: 100%; }}
      .card .label {{ font-size: .78rem; font-weight: 500; color: {SUBTLE}; margin-bottom: 8px; }}
      .card .value {{ font-size: 1.9rem; font-weight: 600; letter-spacing: -.01em; color: {INK}; line-height: 1.12; }}
      .card .sub {{ font-size: .85rem; color: {SUBTLE}; margin-top: 6px; }}

      .splitbar {{ display: flex; height: 54px; border-radius: 14px; overflow: hidden;
        font-weight: 500; color: #fff; font-size: .95rem; }}
      .splitbar span {{ display: flex; align-items: center; justify-content: center; min-width: 42px; }}

      .stButton > button {{ background: {ACCENT}; color: #fff; border: none; border-radius: 980px;
        padding: .5rem 1.4rem; font-weight: 400; font-size: 1rem; transition: background .15s ease; }}
      .stButton > button:hover {{ background: #0077ed; color: #fff; }}

      .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 6px; }}
      [data-testid="stMetricValue"] {{ color: {INK}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def style_fig(fig, height=380):
    """Apply a clean, Apple-like layout to any Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=34, b=8),
        font=dict(family=APPLE_FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=15, color=INK),
        xaxis=dict(gridcolor="#e8e8ed", zeroline=False, linecolor="#d2d2d7"),
        yaxis=dict(gridcolor="#e8e8ed", zeroline=False, linecolor="#d2d2d7"),
    )
    return fig


def card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'


TEAMS = list_teams()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Data")
    st.caption("Model trained on 150+ years of international results (Kaggle).")
    if st.button("Pull latest results & retrain"):
        from refresh_data import refresh
        from train_model import train
        with st.spinner("Downloading latest data from Kaggle..."):
            refresh()
        with st.spinner("Retraining model..."):
            train()
        st.cache_data.clear()
        st.success("Refreshed and retrained. Reload the page.")

st.markdown(
    '<div class="hero"><h1>World Cup 2026</h1>'
    "<p>Elo-powered match predictions, a Monte Carlo tournament simulator, and a historical "
    "vault — driven by one live-updating dataset.</p></div>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs(["Match Predictor", "Tournament Simulator", "Historical Vault"])

# ================================================================ TAB 1
with tab1:
    st.subheader("Head-to-head match predictor")
    c1, c2 = st.columns(2)
    default_a = TEAMS.index("Brazil") if "Brazil" in TEAMS else 0
    default_b = TEAMS.index("France") if "France" in TEAMS else 1
    team_a = c1.selectbox("Team A", TEAMS, index=default_a)
    team_b = c2.selectbox("Team B", TEAMS, index=default_b)

    if st.button("Simulate Match", type="primary"):
        if team_a == team_b:
            st.warning("Pick two different teams.")
        else:
            with st.spinner("Running the model..."):
                p = predict_match(team_a, team_b, neutral=True)
                form_a, form_b = get_recent_form(team_a), get_recent_form(team_b)
                rating_a, rating_b = get_team_rating(team_a), get_team_rating(team_b)

            pa, pd_, pb = p["a"] * 100, p["draw"] * 100, p["b"] * 100
            col_a, col_b = team_color(team_a), team_color(team_b)
            st.markdown(
                f'<div class="splitbar">'
                f'<span style="width:{pa}%;background:{col_a}">{team_a} {pa:.0f}%</span>'
                f'<span style="width:{pd_}%;background:#7a7a7a">Draw {pd_:.0f}%</span>'
                f'<span style="width:{pb}%;background:{col_b}">{team_b} {pb:.0f}%</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.write("")

            m1, m2, m3 = st.columns(3)
            m1.markdown(card(f"{team_a} win", f"{pa:.1f}%"), unsafe_allow_html=True)
            m2.markdown(card("Draw", f"{pd_:.1f}%"), unsafe_allow_html=True)
            m3.markdown(card(f"{team_b} win", f"{pb:.1f}%"), unsafe_allow_html=True)

            st.markdown("###### Key predictive factors")
            f1, f2, f3 = st.columns(3)
            f1.markdown(
                card("Power rating (Elo)", f"{rating_a:.0f} vs {rating_b:.0f}",
                     f"Edge: {team_a if rating_a >= rating_b else team_b} (+{abs(rating_a-rating_b):.0f})"),
                unsafe_allow_html=True,
            )
            f2.markdown(
                card(f"{team_a} recent form", f"{form_a['points']}/30 pts",
                     f"{form_a['wins']}W-{form_a['draws']}D-{form_a['losses']}L (last {form_a['played']})"),
                unsafe_allow_html=True,
            )
            f3.markdown(
                card(f"{team_b} recent form", f"{form_b['points']}/30 pts",
                     f"{form_b['wins']}W-{form_b['draws']}D-{form_b['losses']}L (last {form_b['played']})"),
                unsafe_allow_html=True,
            )
            st.caption("Neutral venue assumed. Ratings & form are computed from our own match data.")

# ================================================================ TAB 2
with tab2:
    st.subheader("Monte Carlo tournament simulator")
    st.caption(
        "Plays the rest of the World Cup thousands of times. Matches on or before the "
        "**as-of date** are locked to real results; everything after is simulated. Drag "
        "the date back to replay the tournament from an earlier point."
    )
    ctrl1, ctrl2 = st.columns([2, 1])
    n_iter = ctrl1.slider("Simulations", min_value=500, max_value=10000, value=2000, step=500)
    as_of = ctrl2.date_input(
        "As-of date",
        value=date(2026, 7, 6),
        min_value=date(2026, 6, 11),
        max_value=date(2026, 7, 6),
    )

    if st.button("Execute Tournament Monte Carlo", type="primary"):
        progress = st.progress(0.0, text="Simulating...")
        result = run_monte_carlo(n_iter, as_of=as_of, progress_cb=lambda f: progress.progress(f, text=f"Simulating... {f*100:.0f}%"))
        progress.empty()

        top = result[result["Title %"] > 0].head(15)
        fig = px.bar(top.sort_values("Title %"), x="Title %", y="Team", orientation="h", text="Title %")
        fig.update_traces(marker_color=ACCENT, marker_line_width=0,
                          texttemplate="%{text:.1f}%", textposition="outside",
                          textfont_color=INK, cliponaxis=False,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        style_fig(fig, height=470)
        fig.update_layout(showlegend=False, xaxis_title="Title probability", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("###### Full probability table")
        st.dataframe(
            result.style.format({"Advance %": "{:.1f}", "Semifinal %": "{:.1f}", "Title %": "{:.1f}"}),
            use_container_width=True, height=420,
        )

# ================================================================ TAB 3
with tab3:
    st.subheader("Historical World Cup vault")
    country = st.selectbox("Choose a nation", TEAMS, index=TEAMS.index("Brazil") if "Brazil" in TEAMS else 0)
    hist = wc_history(country)

    if hist["matches"] == 0:
        st.info(f"{country} has no World Cup finals matches in the dataset.")
    else:
        h1, h2, h3, h4 = st.columns(4)
        h1.markdown(card("Appearances", str(hist["appearances"]), "distinct editions"), unsafe_allow_html=True)
        h2.markdown(card("Matches / Wins", f"{hist['matches']} / {hist['wins']}", f"{hist['win_rate']:.0f}% win rate"), unsafe_allow_html=True)
        h3.markdown(card("Goals scored", str(hist["goals_for"]), f"{hist['goals_against']} conceded"), unsafe_allow_html=True)
        h4.markdown(card("Current power rating", f"{get_team_rating(country):.0f}", "live Elo"), unsafe_allow_html=True)

        left, right = st.columns(2)
        goals_df = wc_goals_by_year(country)
        if not goals_df.empty:
            gfig = px.line(goals_df, x="year", y="goals", markers=True)
            gfig.update_traces(line_color=ACCENT, line_width=2.5, marker_size=7,
                               hovertemplate="%{x}: %{y} goals<extra></extra>")
            style_fig(gfig, height=340)
            gfig.update_layout(title="Goals scored per World Cup", xaxis_title="", yaxis_title="goals")
            left.plotly_chart(gfig, use_container_width=True)

        # Power rating vs the field: where this nation's live Elo sits among all teams.
        ratings = sorted(((t, get_team_rating(t)) for t in TEAMS), key=lambda x: x[1], reverse=True)
        rank = [t for t, _ in ratings].index(country) + 1
        avg_rating = sum(r for _, r in ratings) / len(ratings)
        comp = pd.DataFrame({
            "Metric": [country, "Field average"],
            "Power rating": [get_team_rating(country), avg_rating],
        })
        cfig = go.Figure(go.Bar(
            x=comp["Power rating"], y=comp["Metric"], orientation="h",
            marker_color=[ACCENT, "#d2d2d7"], marker_line_width=0,
            hovertemplate="%{y}: %{x:.0f}<extra></extra>",
        ))
        style_fig(cfig, height=340)
        cfig.update_layout(title=f"Power rating vs field (ranked #{rank} of {len(TEAMS)})",
                           xaxis_title="Elo", yaxis_title="")
        right.plotly_chart(cfig, use_container_width=True)
        st.caption("Best-finish/stage data isn't in the source dataset, so the vault reports "
                   "robustly-derivable finals stats (appearances, record, goals).")
