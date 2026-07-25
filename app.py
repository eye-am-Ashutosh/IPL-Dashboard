"""
IPL Deliveries Dashboard
------------------------
Run locally:
    pip install -r dashboard/requirements.txt
    streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from metrics import (
    batter_stats,
    bowler_stats,
    chase_defend_summary,
    head_to_head,
    match_results,
    normalize_teams,
    normalize_venues,
    phase_batting_leaders,
    phase_bowling_leaders,
    phase_stats,
    run_distribution,
    season_overview,
    team_batting,
    team_records,
    top_innings,
    venue_overview,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "ipl_deliveries_real (1).csv.gz"
FALLBACK_DATA = ROOT / "ipl_deliveries_real (1).csv"


@st.cache_data(show_spinner="Loading IPL delivery data…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_venues(normalize_teams(df))


def filter_data(
    df: pd.DataFrame,
    seasons: list[str],
    teams: list[str],
) -> pd.DataFrame:
    filtered = df[df["season"].isin(seasons)]
    if teams:
        filtered = filtered[
            filtered["batting_team"].isin(teams) | filtered["bowling_team"].isin(teams)
        ]
    return filtered


def overview_metrics(df: pd.DataFrame) -> dict[str, int | float]:
    legal = df.loc[df["is_legal_delivery"] == 1]
    return {
        "matches": int(df["match_id"].nunique()),
        "deliveries": len(df),
        "runs": int(df["total_runs"].sum()),
        "wickets": int(df["is_wicket"].sum()),
        "dot_pct": round((legal["total_runs"] == 0).mean() * 100, 1),
        "boundary_pct": round(
            ((legal["batsman_runs"] == 4) | (legal["batsman_runs"] == 6)).mean() * 100,
            1,
        ),
    }


def main() -> None:
    st.set_page_config(
        page_title="IPL Deliveries Dashboard",
        page_icon="🏏",
        layout="wide",
    )

    st.title("IPL Deliveries Dashboard")
    st.caption("Ball-by-ball analysis across IPL seasons (2007/08 – 2026)")

    data_path = DEFAULT_DATA if DEFAULT_DATA.exists() else FALLBACK_DATA
    if not data_path.exists():
        st.error("Could not find ipl_deliveries_real CSV in the project root.")
        st.stop()

    df_all = load_data(str(data_path))

    with st.sidebar:
        st.header("Filters")
        seasons = st.multiselect(
            "Season",
            options=sorted(df_all["season"].unique(), key=str),
            default=sorted(df_all["season"].unique(), key=str),
        )
        teams = st.multiselect(
            "Team",
            options=sorted(df_all["batting_team"].unique()),
            default=[],
            placeholder="All teams",
        )
        min_balls = st.slider("Min balls (player tables)", 100, 1000, 300, step=50)
        st.divider()
        st.caption(f"Data source: `{data_path.name}`")

    if not seasons:
        st.warning("Select at least one season.")
        st.stop()

    df = filter_data(df_all, seasons, teams)
    if df.empty:
        st.warning("No deliveries match the current filters.")
        st.stop()

    metrics = overview_metrics(df)
    chase = chase_defend_summary(df)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Matches", f"{metrics['matches']:,}")
    c2.metric("Deliveries", f"{metrics['deliveries']:,}")
    c3.metric("Total runs", f"{metrics['runs']:,}")
    c4.metric("Wickets", f"{metrics['wickets']:,}")
    c5.metric("Dot ball %", f"{metrics['dot_pct']}%")
    c6.metric("Boundary %", f"{metrics['boundary_pct']}%")

    (
        tab_overview,
        tab_batting,
        tab_bowling,
        tab_teams,
        tab_innings,
        tab_outcomes,
        tab_venues,
    ) = st.tabs(
        [
            "Overview",
            "Batting",
            "Bowling",
            "Teams",
            "Top Innings",
            "Match Outcomes",
            "Venues",
        ]
    )

    with tab_overview:
        left, right = st.columns(2)

        with left:
            st.subheader("Scoring trend by season")
            season_df = season_overview(df)
            fig_season = px.bar(
                season_df,
                x="season",
                y="avg_runs_per_match",
                text="avg_runs_per_match",
                labels={"season": "Season", "avg_runs_per_match": "Avg runs / match"},
                color="avg_runs_per_match",
                color_continuous_scale="Oranges",
            )
            fig_season.update_traces(texttemplate="%{text}", textposition="outside")
            fig_season.update_layout(coloraxis_showscale=False, height=420)
            st.plotly_chart(fig_season, use_container_width=True)

        with right:
            st.subheader("Runs per ball by phase")
            phase_df = phase_stats(df)
            fig_phase = px.bar(
                phase_df,
                x="phase",
                y="runs_per_ball",
                text="runs_per_ball",
                labels={"phase": "", "runs_per_ball": "Runs per ball"},
                color="runs_per_ball",
                color_continuous_scale="Blues",
            )
            fig_phase.update_traces(texttemplate="%{text}", textposition="outside")
            fig_phase.update_layout(coloraxis_showscale=False, height=420)
            st.plotly_chart(fig_phase, use_container_width=True)

        st.subheader("Run distribution")
        runs_df = run_distribution(df)
        fig_runs = px.bar(
            runs_df,
            x="runs",
            y="deliveries",
            text="share_pct",
            labels={"runs": "Runs off delivery", "deliveries": "Count", "share_pct": "Share %"},
        )
        fig_runs.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig_runs, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Dismissal types")
            dismissals = (
                df.loc[df["is_wicket"] == 1, "dismissal_kind"]
                .value_counts()
                .head(8)
                .reset_index()
            )
            dismissals.columns = ["dismissal", "count"]
            fig_dismissals = px.pie(
                dismissals,
                names="dismissal",
                values="count",
                hole=0.45,
            )
            st.plotly_chart(fig_dismissals, use_container_width=True)

        with col_b:
            st.subheader("Chase vs defend")
            outcome_df = pd.DataFrame(
                {
                    "Outcome": ["Chase wins", "Defend wins"],
                    "Matches": [chase["chase_wins"], chase["defend_wins"]],
                }
            )
            fig_outcome = px.pie(
                outcome_df,
                names="Outcome",
                values="Matches",
                hole=0.45,
                color="Outcome",
                color_discrete_map={"Chase wins": "#2ecc71", "Defend wins": "#3498db"},
            )
            st.plotly_chart(fig_outcome, use_container_width=True)

        st.subheader("Extras breakdown")
        extras = {
            "Wides": int(df["wides"].sum()),
            "No balls": int(df["noballs"].sum()),
            "Byes": int(df["byes"].sum()),
            "Leg byes": int(df["legbyes"].sum()),
        }
        extras_df = pd.DataFrame(list(extras.items()), columns=["Type", "Count"])
        extras_col1, extras_col2 = st.columns([1, 2])
        with extras_col1:
            st.dataframe(extras_df, hide_index=True, use_container_width=True)
        with extras_col2:
            fig_extras = px.bar(
                extras_df,
                x="Count",
                y="Type",
                orientation="h",
                color="Type",
                labels={"Type": ""},
            )
            fig_extras.update_layout(showlegend=False, height=280)
            st.plotly_chart(fig_extras, use_container_width=True)

    with tab_batting:
        batting_df = df[df["batting_team"].isin(teams)] if teams else df
        batters = batter_stats(batting_df, min_balls=min_balls)
        st.subheader("Top run-scorers")
        st.dataframe(
            batters[
                [
                    "batter",
                    "runs",
                    "balls",
                    "average",
                    "strike_rate",
                    "fours",
                    "sixes",
                    "dismissals",
                ]
            ].head(25),
            hide_index=True,
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            top_runs = batters.nlargest(12, "runs").sort_values("runs")
            fig_runs_bar = px.bar(
                top_runs,
                x="runs",
                y="batter",
                orientation="h",
                labels={"runs": "Runs", "batter": ""},
                color="runs",
                color_continuous_scale="Greens",
            )
            fig_runs_bar.update_layout(coloraxis_showscale=False, height=480)
            st.plotly_chart(fig_runs_bar, use_container_width=True)

        with col2:
            st.caption("Average vs strike rate, among the top run-scorers above")
            sr_pool = batters.nlargest(15, "runs")
            fig_sr = px.scatter(
                sr_pool,
                x="average",
                y="strike_rate",
                size="runs",
                color="strike_rate",
                hover_name="batter",
                labels={"average": "Average", "strike_rate": "Strike rate"},
                color_continuous_scale="Viridis",
            )
            st.plotly_chart(fig_sr, use_container_width=True)

        st.divider()
        st.subheader("Phase specialists")
        phase_min_balls = max(20, min_balls // 5)
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            st.markdown("**Top powerplay scorers** (overs 1-6)")
            pp_batters = phase_batting_leaders(batting_df, "powerplay", min_balls=phase_min_balls)
            if pp_batters.empty:
                st.info("Not enough powerplay balls faced at this filter to rank batters.")
            else:
                fig_pp_bat = px.bar(
                    pp_batters.head(10).sort_values("strike_rate"),
                    x="strike_rate",
                    y="batter",
                    orientation="h",
                    hover_data=["runs", "balls"],
                    labels={"strike_rate": "Strike rate", "batter": ""},
                    color="strike_rate",
                    color_continuous_scale="Blues",
                )
                fig_pp_bat.update_layout(coloraxis_showscale=False, height=380)
                st.plotly_chart(fig_pp_bat, use_container_width=True)

        with pcol2:
            st.markdown("**Top finishers** (best strike rate, overs 16-20)")
            death_batters = phase_batting_leaders(batting_df, "death", min_balls=phase_min_balls)
            if death_batters.empty:
                st.info("Not enough death-overs balls faced at this filter to rank batters.")
            else:
                fig_death_bat = px.bar(
                    death_batters.head(10).sort_values("strike_rate"),
                    x="strike_rate",
                    y="batter",
                    orientation="h",
                    hover_data=["runs", "balls"],
                    labels={"strike_rate": "Strike rate", "batter": ""},
                    color="strike_rate",
                    color_continuous_scale="Oranges",
                )
                fig_death_bat.update_layout(coloraxis_showscale=False, height=380)
                st.plotly_chart(fig_death_bat, use_container_width=True)

    with tab_bowling:
        bowling_df = df[df["bowling_team"].isin(teams)] if teams else df
        bowlers = bowler_stats(bowling_df, min_balls=min_balls)
        st.subheader("Top wicket-takers")
        st.dataframe(
            bowlers[
                [
                    "bowler",
                    "wickets",
                    "balls",
                    "economy",
                    "average",
                    "strike_rate",
                    "runs_conceded",
                ]
            ].head(25),
            hide_index=True,
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            top_wkts = bowlers.nlargest(12, "wickets").sort_values("wickets")
            fig_wkts = px.bar(
                top_wkts,
                x="wickets",
                y="bowler",
                orientation="h",
                labels={"wickets": "Wickets", "bowler": ""},
                color="wickets",
                color_continuous_scale="Reds",
            )
            fig_wkts.update_layout(coloraxis_showscale=False, height=480)
            st.plotly_chart(fig_wkts, use_container_width=True)

        with col2:
            st.caption("Economy vs average, among the top wicket-takers above")
            econ_pool = bowlers.nlargest(15, "wickets")
            fig_econ = px.scatter(
                econ_pool,
                x="economy",
                y="average",
                size="wickets",
                color="economy",
                hover_name="bowler",
                labels={"economy": "Economy", "average": "Bowling average"},
                color_continuous_scale="RdYlGn_r",
            )
            st.plotly_chart(fig_econ, use_container_width=True)

        st.divider()
        st.subheader("Phase specialists")
        phase_min_balls = max(20, min_balls // 5)
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            st.markdown("**Best powerplay economy** (overs 1-6)")
            pp_bowlers = phase_bowling_leaders(bowling_df, "powerplay", min_balls=phase_min_balls)
            if pp_bowlers.empty:
                st.info("Not enough powerplay balls bowled at this filter to rank bowlers.")
            else:
                fig_pp_bowl = px.bar(
                    pp_bowlers.head(10).sort_values("economy", ascending=False),
                    x="economy",
                    y="bowler",
                    orientation="h",
                    hover_data=["wickets", "balls"],
                    labels={"economy": "Economy", "bowler": ""},
                    color="economy",
                    color_continuous_scale="RdYlGn_r",
                )
                fig_pp_bowl.update_layout(coloraxis_showscale=False, height=380)
                st.plotly_chart(fig_pp_bowl, use_container_width=True)

        with pcol2:
            st.markdown("**Best death-overs economy** (overs 16-20)")
            death_bowlers = phase_bowling_leaders(bowling_df, "death", min_balls=phase_min_balls)
            if death_bowlers.empty:
                st.info("Not enough death-overs balls bowled at this filter to rank bowlers.")
            else:
                fig_death_bowl = px.bar(
                    death_bowlers.head(10).sort_values("economy", ascending=False),
                    x="economy",
                    y="bowler",
                    orientation="h",
                    hover_data=["wickets", "balls"],
                    labels={"economy": "Economy", "bowler": ""},
                    color="economy",
                    color_continuous_scale="RdYlGn_r",
                )
                fig_death_bowl.update_layout(coloraxis_showscale=False, height=380)
                st.plotly_chart(fig_death_bowl, use_container_width=True)

    with tab_teams:
        team_only_df = df[df["batting_team"].isin(teams)] if teams else df
        teams_df = team_batting(team_only_df)
        st.subheader("Team batting totals" if not teams else "Selected team totals")
        st.dataframe(teams_df, hide_index=True, use_container_width=True)

        fig_teams = px.bar(
            teams_df.sort_values("runs"),
            x="runs",
            y="batting_team",
            orientation="h",
            labels={"runs": "Total runs", "batting_team": ""},
            color="runs",
            color_continuous_scale="Purples",
        )
        fig_teams.update_layout(coloraxis_showscale=False, height=max(420, len(teams_df) * 28))
        st.plotly_chart(fig_teams, use_container_width=True)

        if len(teams) == 1:
            st.divider()
            st.subheader(f"Head-to-head: {teams[0]} vs each opponent")
            h2h = head_to_head(match_results(df), teams[0])
            if h2h.empty:
                st.info("No decided matches for this team under the current filters.")
            else:
                st.dataframe(h2h, hide_index=True, use_container_width=True)
                fig_h2h = px.bar(
                    h2h.sort_values("played"),
                    x=["wins", "losses"],
                    y="opponent",
                    orientation="h",
                    labels={"value": "Matches", "opponent": "", "variable": ""},
                    color_discrete_map={"wins": "#2ecc71", "losses": "#e74c3c"},
                )
                fig_h2h.update_layout(height=max(420, len(h2h) * 32), barmode="stack")
                st.plotly_chart(fig_h2h, use_container_width=True)
        elif len(teams) > 1:
            st.caption("Select exactly one team in the sidebar to see its head-to-head record.")

    with tab_innings:
        innings_df = top_innings(df)
        st.subheader("Highest team innings")
        st.dataframe(
            innings_df[["season", "batting_team", "scorecard", "match_id"]],
            hide_index=True,
            use_container_width=True,
        )

        fig_innings = px.bar(
            innings_df.sort_values("total"),
            x="total",
            y="batting_team",
            orientation="h",
            color="season",
            hover_data=["wickets", "match_id"],
            labels={"total": "Runs", "batting_team": ""},
        )
        st.plotly_chart(fig_innings, use_container_width=True)

    with tab_outcomes:
        results = match_results(df)
        decided = results.dropna(subset=["winner"])
        records = team_records(results)

        st.subheader("Team win/loss record")
        st.dataframe(records, hide_index=True, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig_wins = px.bar(
                records.sort_values("wins"),
                x="wins",
                y="team",
                orientation="h",
                labels={"wins": "Wins", "team": ""},
                color="win_pct",
                color_continuous_scale="Tealgrn",
            )
            fig_wins.update_layout(height=max(420, len(records) * 28))
            st.plotly_chart(fig_wins, use_container_width=True)

        with col2:
            st.subheader("How matches were decided")
            result_counts = decided["result_type"].value_counts().reset_index()
            result_counts.columns = ["result_type", "count"]
            fig_result = px.pie(
                result_counts,
                names="result_type",
                values="count",
                hole=0.45,
            )
            st.plotly_chart(fig_result, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Biggest wins by runs")
            by_runs = decided[decided["result_type"] == "Won batting 1st (runs)"].nlargest(
                10, "margin"
            )
            st.dataframe(
                by_runs[["season", "winner", "team1", "team2", "margin"]].rename(
                    columns={"margin": "margin (runs)"}
                ),
                hide_index=True,
                use_container_width=True,
            )

        with col4:
            st.subheader("Biggest wins by wickets")
            by_wkts = decided[decided["result_type"] == "Won batting 2nd (wickets)"].nlargest(
                10, "margin"
            )
            st.dataframe(
                by_wkts[["season", "winner", "team1", "team2", "margin"]].rename(
                    columns={"margin": "margin (wickets)"}
                ),
                hide_index=True,
                use_container_width=True,
            )

        no_result = len(results) - len(decided)
        if no_result:
            st.caption(f"{no_result} match(es) with no result / tie without a Super Over.")

    with tab_venues:
        venues_df = venue_overview(df)
        st.subheader("Venue averages")
        st.dataframe(
            venues_df.rename(
                columns={
                    "avg_innings_score": "avg innings score",
                    "highest_innings": "highest innings",
                    "avg_wickets_per_innings": "avg wickets/innings",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

        top_venues = venues_df.nlargest(15, "matches").sort_values("avg_innings_score")
        fig_venues = px.bar(
            top_venues,
            x="avg_innings_score",
            y="venue",
            orientation="h",
            hover_data=["matches", "highest_innings"],
            labels={"avg_innings_score": "Avg innings score", "venue": ""},
            color="avg_innings_score",
            color_continuous_scale="Tealrose",
        )
        fig_venues.update_layout(
            coloraxis_showscale=False, height=max(420, len(top_venues) * 28)
        )
        st.plotly_chart(fig_venues, use_container_width=True)
        st.caption(
            "Top 15 venues by matches played under the current filters, ranked by average innings score."
        )


if __name__ == "__main__":
    main()
