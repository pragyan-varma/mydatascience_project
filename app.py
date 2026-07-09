import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from constants import team_color, team_flag, team_gradient, team_secondary  # noqa: E402
from history import wc_goals_by_year, wc_history  # noqa: E402
from predictor import (  # noqa: E402
    get_recent_form,
    get_team_rating,
    list_teams,
    predict_match,
)
from simulator import run_monte_carlo  # noqa: E402

st.set_page_config(page_title="World Cup 2026 Analytics", page_icon="⚽", layout="wide")

# ============================================================ design tokens
FONT = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif'
INK = "#f8fafc"
SUBTLE = "#94a3b8"
ACCENT = "#6ea8fe"
GRID = "rgba(148,163,184,0.14)"

# ============================================================ global CSS (st.html)
st.html(
    f"""
    <style>
      html, body, .stApp, [class*="css"], button, input, select, textarea {{
        font-family: {FONT} !important;
        -webkit-font-smoothing: antialiased;
      }}
      .stApp {{
        background: linear-gradient(160deg, #1e293b 0%, #0f172a 60%, #0b1120 100%);
        background-attachment: fixed;
        color: #e2e8f0;
      }}
      .block-container {{ max-width: 1180px; padding-top: 1.4rem; }}

      * {{ transition: all 0.4s cubic-bezier(0.25, 1, 0.5, 1); }}
      @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(16px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes growBar {{ from {{ width: 0; }} to {{ width: var(--w); }} }}
      @keyframes shimmer {{ to {{ background-position: 200% center; }} }}

      /* ---- typography hierarchy ---- */
      .hero {{ text-align: center; padding: 46px 20px 26px; animation: fadeInUp .6s both; }}
      .hero h1 {{ margin: 0; font-size: 3.4rem; font-weight: 800; letter-spacing: -0.03em;
        color: {INK}; line-height: 1.02; }}
      .hero p {{ margin: 14px auto 0; max-width: 640px; font-size: 1.18rem; font-weight: 400;
        color: {SUBTLE}; line-height: 1.45; }}
      h2, h3 {{ color: {INK} !important; font-weight: 700 !important; letter-spacing: -0.02em; }}
      .section-sub {{ color: {SUBTLE}; font-weight: 500; font-size: .95rem; margin: -6px 0 14px; }}

      /* ---- glass card modules ---- */
      .glass {{
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px; padding: 24px; height: 100%;
        box-shadow: 0 10px 34px rgba(0,0,0,0.28);
        animation: fadeInUp .5s both;
      }}
      .glass .label {{ font-size: .74rem; font-weight: 600; letter-spacing: .04em;
        text-transform: uppercase; color: {SUBTLE}; margin-bottom: 10px; }}
      .glass .callout {{ font-size: 2.9rem; font-weight: 800; letter-spacing: -0.03em;
        color: {INK}; line-height: 1; }}
      .glass .sub {{ font-size: .86rem; color: {SUBTLE}; margin-top: 8px; font-weight: 400; }}

      /* ---- animated split prediction bar ---- */
      .splitbar {{ display: flex; height: 58px; border-radius: 14px; overflow: hidden;
        font-weight: 600; color: #fff; font-size: .95rem; box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        animation: fadeInUp .5s both; }}
      .splitbar span {{ display: flex; align-items: center; justify-content: center;
        width: var(--w); white-space: nowrap; overflow: hidden;
        animation: growBar .9s cubic-bezier(0.25, 1, 0.5, 1); }}

      /* ---- hero country banner (Tab 3) ---- */
      .country-hero {{ border-radius: 18px; padding: 30px 34px; margin-bottom: 6px;
        display: flex; align-items: center; gap: 22px; animation: fadeInUp .5s both;
        box-shadow: 0 14px 40px rgba(0,0,0,0.35); }}
      .country-hero .flag {{ font-size: 3.4rem; line-height: 1; }}
      .country-hero .name {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em;
        color: #fff; margin: 0; }}
      .country-hero .tag {{ color: rgba(255,255,255,0.85); font-weight: 500; margin-top: 2px; }}

      /* ---- shimmer loading text ---- */
      .shimmer {{ font-size: 1.05rem; font-weight: 600; letter-spacing: -0.01em;
        background: linear-gradient(90deg, {SUBTLE} 0%, #fff 50%, {SUBTLE} 100%);
        background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; animation: shimmer 1.6s linear infinite; }}

      /* ---- buttons ---- */
      .stButton > button {{ background: {ACCENT}; color: #06122b; border: none; border-radius: 980px;
        padding: .55rem 1.5rem; font-weight: 600; font-size: 1rem; }}
      .stButton > button:hover {{ transform: scale(1.02); background: #8bbcff;
        box-shadow: 0 8px 22px rgba(110,168,254,0.35); }}

      .stTabs [data-baseweb="tab-list"] {{ justify-content: center; gap: 8px; }}
      [data-testid="stMetricValue"] {{ color: {INK}; }}
    </style>
    """
)


def glass_card(label, value, sub="", accent=None):
    """A glassmorphism metric module. `accent` adds a colored top border + glow."""
    style = ""
    if accent:
        style = f"border-top: 3px solid {accent}; box-shadow: 0 10px 34px rgba(0,0,0,0.28), 0 0 26px -8px {accent};"
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="glass" style="{style}"><div class="label">{label}</div>'
            f'<div class="callout">{value}</div>{sub_html}</div>')


def style_fig(fig, height=380):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=36, b=8),
        font=dict(family=FONT, color="#e2e8f0", size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=15, color=INK),
        xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID),
    )
    return fig


TEAMS = list_teams()

# ============================================================ sidebar
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

# ============================================================ hero
st.html(
    '<div class="hero"><h1>World Cup 2026</h1>'
    "<p>Elo-powered match predictions, a Monte Carlo tournament simulator, and a historical "
    "vault — driven by one live-updating dataset.</p></div>"
)

tab1, tab2, tab3 = st.tabs(["Match Predictor", "Tournament Simulator", "Historical Vault"])

# ================================================================ TAB 1
with tab1:
    st.subheader("Head-to-head match predictor")
    st.markdown('<div class="section-sub">Two nations, one neutral-venue simulation.</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    default_a = TEAMS.index("Brazil") if "Brazil" in TEAMS else 0
    default_b = TEAMS.index("France") if "France" in TEAMS else 1
    team_a = c1.selectbox("Team A", TEAMS, index=default_a, key="team_a")
    team_b = c2.selectbox("Team B", TEAMS, index=default_b, key="team_b")

    if st.button("Simulate Match", type="primary", key="sim_match"):
        if team_a == team_b:
            st.warning("Pick two different teams.")
        else:
            with st.spinner("Running the model..."):
                p = predict_match(team_a, team_b, neutral=True)
                form_a, form_b = get_recent_form(team_a), get_recent_form(team_b)
                rating_a, rating_b = get_team_rating(team_a), get_team_rating(team_b)

            pa, pdr, pb = p["a"] * 100, p["draw"] * 100, p["b"] * 100
            col_a, col_b = team_color(team_a), team_color(team_b)
            st.html(
                f'<div class="splitbar">'
                f'<span style="--w:{pa}%;background:{col_a}">{team_flag(team_a)} {team_a} {pa:.0f}%</span>'
                f'<span style="--w:{pdr}%;background:#475569">Draw {pdr:.0f}%</span>'
                f'<span style="--w:{pb}%;background:{col_b}">{team_flag(team_b)} {team_b} {pb:.0f}%</span>'
                f"</div>"
            )
            st.write("")

            m1, m2, m3 = st.columns(3)
            m1.markdown(glass_card(f"{team_flag(team_a)} {team_a} win", f"{pa:.1f}%", accent=col_a),
                        unsafe_allow_html=True)
            m2.markdown(glass_card("Draw", f"{pdr:.1f}%"), unsafe_allow_html=True)
            m3.markdown(glass_card(f"{team_flag(team_b)} {team_b} win", f"{pb:.1f}%", accent=col_b),
                        unsafe_allow_html=True)

            st.markdown("###### Key predictive factors")
            f1, f2, f3 = st.columns(3)
            edge_team = team_a if rating_a >= rating_b else team_b
            f1.markdown(
                glass_card("Power rating edge", f"+{abs(rating_a - rating_b):.0f}",
                           f"{team_flag(edge_team)} {edge_team} · {rating_a:.0f} vs {rating_b:.0f} Elo",
                           accent=team_color(edge_team)),
                unsafe_allow_html=True)
            f2.markdown(
                glass_card(f"{team_a} form", f"{form_a['points']}/30",
                           f"{form_a['wins']}W-{form_a['draws']}D-{form_a['losses']}L · last {form_a['played']}",
                           accent=col_a),
                unsafe_allow_html=True)
            f3.markdown(
                glass_card(f"{team_b} form", f"{form_b['points']}/30",
                           f"{form_b['wins']}W-{form_b['draws']}D-{form_b['losses']}L · last {form_b['played']}",
                           accent=col_b),
                unsafe_allow_html=True)
            st.caption("Neutral venue assumed. Ratings & form are computed from our own match data.")

# ================================================================ TAB 2
with tab2:
    st.subheader("Monte Carlo tournament simulator")
    st.markdown(
        '<div class="section-sub">Matches on or before the as-of date are locked to real results; '
        "everything after is simulated. Drag the date back to replay from an earlier point.</div>",
        unsafe_allow_html=True)

    ctrl1, ctrl2 = st.columns([2, 1])
    n_iter = ctrl1.slider("Simulations", 500, 10000, 2000, 500, key="sim_iters")
    as_of = ctrl2.date_input("As-of date", value=date(2026, 7, 6),
                             min_value=date(2026, 6, 11), max_value=date(2026, 7, 6), key="as_of")

    if st.button("Execute Tournament Monte Carlo", type="primary", key="run_mc"):
        status = st.empty()
        status.html(f'<div class="shimmer">Simulating {n_iter:,} tournament timelines…</div>')
        progress = st.progress(0.0)
        result = run_monte_carlo(n_iter, as_of=as_of, progress_cb=lambda f: progress.progress(f))
        progress.empty()
        status.empty()

        top = result[result["Title %"] > 0].head(15)
        podium = result.head(3)["Team"].tolist()
        p1, p2, p3 = st.columns(3)
        medals = ["Favorite", "Contender", "Dark horse"]
        for col, team, tag in zip([p1, p2, p3], podium, medals):
            row = result[result["Team"] == team].iloc[0]
            col.markdown(glass_card(f"{team_flag(team)} {team}", f"{row['Title %']:.1f}%",
                                    f"{tag} · SF {row['Semifinal %']:.0f}%", accent=team_color(team)),
                         unsafe_allow_html=True)

        st.write("")
        chart_col, table_col = st.columns([3, 2])
        fig = px.bar(top.sort_values("Title %"), x="Title %", y="Team", orientation="h", text="Title %")
        fig.update_traces(marker_color=ACCENT, marker_line_width=0, texttemplate="%{text:.1f}%",
                          textposition="outside", textfont_color=INK, cliponaxis=False,
                          hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
        style_fig(fig, height=470)
        fig.update_layout(showlegend=False, title="Title probability", xaxis_title="", yaxis_title="")
        chart_col.plotly_chart(fig, use_container_width=True)

        with table_col:
            st.markdown('<div class="section-sub">Full field</div>', unsafe_allow_html=True)
            st.dataframe(
                result.style.format({"Advance %": "{:.1f}", "Semifinal %": "{:.1f}", "Title %": "{:.1f}"}),
                use_container_width=True, height=470, hide_index=True)

# ================================================================ TAB 3
with tab3:
    st.subheader("Historical World Cup vault")
    country = st.selectbox("Choose a nation", TEAMS,
                           index=TEAMS.index("Brazil") if "Brazil" in TEAMS else 0, key="vault_country")
    hist = wc_history(country)
    primary = team_color(country)

    st.html(
        f'<div class="country-hero" style="background:{team_gradient(country)};'
        f'border:2px solid {primary};">'
        f'<div class="flag">{team_flag(country)}</div>'
        f'<div><p class="name">{country}</p>'
        f'<div class="tag">Live power rating {get_team_rating(country):.0f} Elo</div></div></div>'
    )

    if hist["matches"] == 0:
        st.info(f"{country} has no World Cup finals matches in the dataset.")
    else:
        h1, h2, h3, h4 = st.columns(4)
        h1.markdown(glass_card("Appearances", str(hist["appearances"]), "distinct editions", accent=primary),
                    unsafe_allow_html=True)
        h2.markdown(glass_card("Wins", f"{hist['wins']}",
                               f"{hist['matches']} played · {hist['win_rate']:.0f}% win rate", accent=primary),
                    unsafe_allow_html=True)
        h3.markdown(glass_card("Goals for", str(hist["goals_for"]),
                               f"{hist['goals_against']} conceded", accent=primary), unsafe_allow_html=True)
        h4.markdown(glass_card("Record", f"{hist['wins']}-{hist['draws']}-{hist['losses']}",
                               "W – D – L all-time", accent=primary), unsafe_allow_html=True)

        left, right = st.columns(2)
        goals_df = wc_goals_by_year(country)
        if not goals_df.empty:
            gfig = px.line(goals_df, x="year", y="goals", markers=True)
            gfig.update_traces(line_color=primary, line_width=2.5, marker_size=7,
                               hovertemplate="%{x}: %{y} goals<extra></extra>")
            style_fig(gfig, height=340)
            gfig.update_layout(title="Goals scored per World Cup", xaxis_title="", yaxis_title="goals")
            left.plotly_chart(gfig, use_container_width=True)

        ratings = sorted(((t, get_team_rating(t)) for t in TEAMS), key=lambda x: x[1], reverse=True)
        rank = [t for t, _ in ratings].index(country) + 1
        avg_rating = sum(r for _, r in ratings) / len(ratings)
        comp = pd.DataFrame({"Metric": [country, "Field average"],
                             "Power rating": [get_team_rating(country), avg_rating]})
        cfig = go.Figure(go.Bar(x=comp["Power rating"], y=comp["Metric"], orientation="h",
                                marker_color=[primary, "#475569"], marker_line_width=0,
                                hovertemplate="%{y}: %{x:.0f}<extra></extra>"))
        style_fig(cfig, height=340)
        cfig.update_layout(title=f"Power rating vs field (ranked #{rank} of {len(TEAMS)})",
                           xaxis_title="Elo", yaxis_title="")
        right.plotly_chart(cfig, use_container_width=True)
        st.caption("Best-finish/stage data isn't in the source dataset, so the vault reports "
                   "robustly-derivable finals stats (appearances, record, goals).")
