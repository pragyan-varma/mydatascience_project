import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from predict import predict_upcoming  # noqa: E402
from refresh_data import refresh  # noqa: E402
from train_model import train  # noqa: E402

st.set_page_config(page_title="World Cup 2026 Match Predictor", layout="wide")
st.title("World Cup 2026 Match Predictor")
st.caption("Trained on 150+ years of international results (via Kaggle), refreshed as real matches happen.")

with st.sidebar:
    st.header("Data")
    if st.button("Pull latest results & retrain"):
        with st.spinner("Downloading latest data from Kaggle..."):
            refresh()
        with st.spinner("Retraining model..."):
            train()
        st.cache_data.clear()
        st.success("Data refreshed and model retrained.")


@st.cache_data(ttl=3600)
def get_predictions() -> pd.DataFrame:
    return predict_upcoming()


preds = get_predictions()

# Home win / Draw / Away win reads as a diverging scale (two opposite poles +
# a neutral middle), so it gets the diverging pair rather than random hues.
OUTCOME_COLORS = {"Home win": "#2a78d6", "Draw": "#898781", "Away win": "#e34948"}

if preds.empty:
    st.info("No upcoming fixtures found in the dataset right now. Click refresh in the sidebar to check for new ones.")
else:
    st.subheader("Upcoming match predictions")
    for _, row in preds.iterrows():
        st.markdown(f"**{row['home_team']} vs {row['away_team']}** — {row['date'].date()} ({row['city']})")
        prob_df = pd.DataFrame(
            {
                "Outcome": [f"{row['home_team']} win", "Draw", f"{row['away_team']} win"],
                "Type": ["Home win", "Draw", "Away win"],
                "Probability": [row["prob_home"], row["prob_draw"], row["prob_away"]],
            }
        )
        fig = px.bar(
            prob_df,
            x="Probability",
            y="Outcome",
            orientation="h",
            range_x=[0, 1],
            color="Type",
            color_discrete_map=OUTCOME_COLORS,
            text_auto=".0%",
        )
        fig.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
            xaxis_tickformat=".0%",
        )
        st.plotly_chart(fig, use_container_width=True)
