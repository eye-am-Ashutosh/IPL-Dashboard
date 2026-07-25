"""Aggregation helpers for the IPL deliveries dashboard."""

from __future__ import annotations

import pandas as pd

TEAM_ALIASES = {
    "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    "Kings XI Punjab": "Punjab Kings",
    "Delhi Daredevils": "Delhi Capitals",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
}


def normalize_teams(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("batting_team", "bowling_team"):
        out[col] = out[col].replace(TEAM_ALIASES)
    return out


VENUE_ALIASES = {
    "Eden Gardens, Kolkata": "Eden Gardens",
    "Wankhede Stadium, Mumbai": "Wankhede Stadium",
    "M Chinnaswamy Stadium, Bengaluru": "M Chinnaswamy Stadium",
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "Feroz Shah Kotla": "Arun Jaitley Stadium, Delhi",
    "Arun Jaitley Stadium": "Arun Jaitley Stadium, Delhi",
    "MA Chidambaram Stadium, Chepauk, Chennai": "MA Chidambaram Stadium, Chepauk",
    "MA Chidambaram Stadium": "MA Chidambaram Stadium, Chepauk",
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": "Rajiv Gandhi International Stadium, Uppal",
    "Rajiv Gandhi International Stadium": "Rajiv Gandhi International Stadium, Uppal",
    "Sawai Mansingh Stadium, Jaipur": "Sawai Mansingh Stadium",
    "Sardar Patel Stadium, Motera": "Narendra Modi Stadium, Ahmedabad",
    "Punjab Cricket Association IS Bindra Stadium, Mohali": "Punjab Cricket Association Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium": "Punjab Cricket Association Stadium, Mohali",
    "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": "Punjab Cricket Association Stadium, Mohali",
    "Zayed Cricket Stadium, Abu Dhabi": "Sheikh Zayed Stadium",
    "Maharashtra Cricket Association Stadium, Pune": "Maharashtra Cricket Association Stadium",
    "Subrata Roy Sahara Stadium": "Maharashtra Cricket Association Stadium",
    "Dr DY Patil Sports Academy, Mumbai": "Dr DY Patil Sports Academy",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium",
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium, Visakhapatnam": (
        "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium"
    ),
    "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh": (
        "Maharaja Yadavindra Singh International Cricket Stadium, Mullanpur"
    ),
    "Himachal Pradesh Cricket Association Stadium, Dharamsala": (
        "Himachal Pradesh Cricket Association Stadium"
    ),
    "Shaheed Veer Narayan Singh International Stadium, Raipur": (
        "Shaheed Veer Narayan Singh International Stadium"
    ),
}


def normalize_venues(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["venue"] = out["venue"].replace(VENUE_ALIASES)
    return out


def season_overview(df: pd.DataFrame) -> pd.DataFrame:
    stats = (
        df.groupby("season", as_index=False)
        .agg(
            matches=("match_id", "nunique"),
            deliveries=("match_id", "count"),
            total_runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
        )
        .sort_values("season")
    )
    stats["avg_runs_per_match"] = (stats["total_runs"] / stats["matches"]).round(1)
    stats["avg_wickets_per_match"] = (stats["wickets"] / stats["matches"]).round(1)
    return stats


def batter_stats(df: pd.DataFrame, min_balls: int = 300) -> pd.DataFrame:
    grouped = (
        df.groupby("batter", as_index=False)
        .agg(
            runs=("batsman_runs", "sum"),
            balls=("is_legal_delivery", "sum"),
            dismissals=("is_wicket", "sum"),
        )
        .query("balls >= @min_balls")
    )
    fours = df.loc[df["batsman_runs"] == 4].groupby("batter").size()
    sixes = df.loc[df["batsman_runs"] == 6].groupby("batter").size()
    grouped["fours"] = grouped["batter"].map(fours).fillna(0).astype(int)
    grouped["sixes"] = grouped["batter"].map(sixes).fillna(0).astype(int)
    grouped["strike_rate"] = (grouped["runs"] / grouped["balls"] * 100).round(1)
    grouped["average"] = (
        grouped["runs"] / grouped["dismissals"].replace(0, pd.NA)
    ).round(1)
    return grouped.sort_values("runs", ascending=False)


def bowler_stats(df: pd.DataFrame, min_balls: int = 300) -> pd.DataFrame:
    grouped = (
        df.groupby("bowler", as_index=False)
        .agg(
            balls=("is_legal_delivery", "sum"),
            runs_conceded=("bowler_runs", "sum"),
            wickets=("is_wicket", "sum"),
            wides=("wides", "sum"),
            noballs=("noballs", "sum"),
        )
        .query("balls >= @min_balls")
    )
    grouped["economy"] = (
        grouped["runs_conceded"] / (grouped["balls"] / 6)
    ).round(2)
    grouped["average"] = (
        grouped["runs_conceded"] / grouped["wickets"].replace(0, pd.NA)
    ).round(1)
    grouped["strike_rate"] = (
        grouped["balls"] / grouped["wickets"].replace(0, pd.NA)
    ).round(1)
    return grouped.sort_values("wickets", ascending=False)


def phase_stats(df: pd.DataFrame) -> pd.DataFrame:
    legal = df.loc[df["is_legal_delivery"] == 1].copy()
    legal["phase"] = pd.cut(
        legal["over"],
        bins=[0, 6, 15, 20],
        labels=["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"],
    )
    phase = (
        legal.groupby("phase", observed=True)
        .agg(
            balls=("total_runs", "count"),
            runs=("total_runs", "sum"),
            wickets=("is_wicket", "sum"),
        )
        .reset_index()
    )
    phase["runs_per_ball"] = (phase["runs"] / phase["balls"]).round(3)
    return phase


def team_batting(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("batting_team", as_index=False)
        .agg(
            runs=("total_runs", "sum"),
            wickets_lost=("is_wicket", "sum"),
            matches=("match_id", "nunique"),
        )
        .sort_values("runs", ascending=False)
    )


def top_innings(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    innings = (
        df.groupby(["match_id", "season", "batting_team"], as_index=False)
        .agg(total=("total_runs", "sum"), wickets=("is_wicket", "sum"))
        .sort_values("total", ascending=False)
        .head(n)
    )
    innings["scorecard"] = (
        innings["total"].astype(str) + "/" + innings["wickets"].astype(str)
    )
    return innings


def chase_defend_summary(df: pd.DataFrame) -> dict[str, int]:
    inning_totals = (
        df.groupby(["match_id", "inning"], as_index=False)
        .agg(score=("total_runs", "sum"))
        .pivot(index="match_id", columns="inning", values="score")
    )
    if 1 not in inning_totals.columns or 2 not in inning_totals.columns:
        return {"chase_wins": 0, "defend_wins": 0}
    chase_wins = int((inning_totals[2] > inning_totals[1]).sum())
    defend_wins = int((inning_totals[1] >= inning_totals[2]).sum())
    return {"chase_wins": chase_wins, "defend_wins": defend_wins}


def match_results(df: pd.DataFrame) -> pd.DataFrame:
    """One row per match: winner, margin, and how the match was decided."""
    innings = (
        df.groupby(["match_id", "season", "inning", "batting_team"], as_index=False)
        .agg(runs=("total_runs", "sum"), wickets=("is_wicket", "sum"))
    )

    rows = []
    for match_id, match_df in innings.groupby("match_id"):
        season = match_df["season"].iloc[0]
        main = match_df[match_df["inning"].isin([1, 2])].sort_values("inning")
        if len(main) < 2:
            rows.append(
                {
                    "match_id": match_id,
                    "season": season,
                    "team1": main["batting_team"].iloc[0] if len(main) else None,
                    "team2": None,
                    "winner": None,
                    "result_type": "No result",
                    "margin": None,
                }
            )
            continue

        team1, team2 = main["batting_team"].iloc[0], main["batting_team"].iloc[1]
        score1, score2 = main["runs"].iloc[0], main["runs"].iloc[1]
        wkts2 = main["wickets"].iloc[1]

        if score1 == score2:
            supers = match_df[match_df["inning"].isin([3, 4, 5, 6])].sort_values("inning")
            if len(supers) >= 2:
                s_team1, s_team2 = supers["batting_team"].iloc[-2], supers["batting_team"].iloc[-1]
                s_score1, s_score2 = supers["runs"].iloc[-2], supers["runs"].iloc[-1]
                winner = s_team1 if s_score1 > s_score2 else s_team2
                rows.append(
                    {
                        "match_id": match_id,
                        "season": season,
                        "team1": team1,
                        "team2": team2,
                        "winner": winner,
                        "result_type": "Super Over",
                        "margin": None,
                    }
                )
            else:
                rows.append(
                    {
                        "match_id": match_id,
                        "season": season,
                        "team1": team1,
                        "team2": team2,
                        "winner": None,
                        "result_type": "Tie (no Super Over)",
                        "margin": None,
                    }
                )
            continue

        if score2 > score1:
            winner, result_type, margin = team2, "Won batting 2nd (wickets)", 10 - wkts2
        else:
            winner, result_type, margin = team1, "Won batting 1st (runs)", score1 - score2

        rows.append(
            {
                "match_id": match_id,
                "season": season,
                "team1": team1,
                "team2": team2,
                "winner": winner,
                "result_type": result_type,
                "margin": margin,
            }
        )

    return pd.DataFrame(rows)


def team_records(results: pd.DataFrame) -> pd.DataFrame:
    """Win/loss record per team from a match_results frame."""
    decided = results.dropna(subset=["winner"])
    teams = pd.unique(decided[["team1", "team2"]].values.ravel())
    teams = [t for t in teams if pd.notna(t)]

    records = []
    for team in teams:
        played = decided[(decided["team1"] == team) | (decided["team2"] == team)]
        wins = int((played["winner"] == team).sum())
        matches = len(played)
        losses = matches - wins
        records.append(
            {
                "team": team,
                "matches": matches,
                "wins": wins,
                "losses": losses,
                "win_pct": round(wins / matches * 100, 1) if matches else 0.0,
            }
        )
    return pd.DataFrame(records).sort_values("wins", ascending=False)


def phase_filter(df: pd.DataFrame, phase: str) -> pd.DataFrame:
    legal = df.loc[df["is_legal_delivery"] == 1]
    if phase == "powerplay":
        return legal[legal["over"] <= 6]
    if phase == "death":
        return legal[legal["over"] > 15]
    raise ValueError(f"Unknown phase: {phase}")


def phase_batting_leaders(df: pd.DataFrame, phase: str, min_balls: int = 60) -> pd.DataFrame:
    """Batter strike rates restricted to a single phase (e.g. death-overs finishers)."""
    phase_df = phase_filter(df, phase)
    grouped = (
        phase_df.groupby("batter", as_index=False)
        .agg(runs=("batsman_runs", "sum"), balls=("batsman_runs", "count"))
        .query("balls >= @min_balls")
    )
    fours = phase_df.loc[phase_df["batsman_runs"] == 4].groupby("batter").size()
    sixes = phase_df.loc[phase_df["batsman_runs"] == 6].groupby("batter").size()
    grouped["fours"] = grouped["batter"].map(fours).fillna(0).astype(int)
    grouped["sixes"] = grouped["batter"].map(sixes).fillna(0).astype(int)
    grouped["strike_rate"] = (grouped["runs"] / grouped["balls"] * 100).round(1)
    return grouped.sort_values("strike_rate", ascending=False)


def phase_bowling_leaders(df: pd.DataFrame, phase: str, min_balls: int = 36) -> pd.DataFrame:
    """Bowling economy restricted to a single phase (e.g. death-overs specialists)."""
    phase_df = phase_filter(df, phase)
    grouped = (
        phase_df.groupby("bowler", as_index=False)
        .agg(balls=("bowler_runs", "count"), runs_conceded=("bowler_runs", "sum"))
        .query("balls >= @min_balls")
    )
    wkts = phase_df.loc[phase_df["is_wicket"] == 1].groupby("bowler").size()
    grouped["wickets"] = grouped["bowler"].map(wkts).fillna(0).astype(int)
    grouped["economy"] = (grouped["runs_conceded"] / (grouped["balls"] / 6)).round(2)
    return grouped.sort_values("economy")


def venue_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Per-venue scoring context: how many matches, and how big an innings typically is."""
    innings = (
        df[df["inning"].isin([1, 2])]
        .groupby(["match_id", "inning", "venue"], as_index=False)
        .agg(runs=("total_runs", "sum"), wickets=("is_wicket", "sum"))
    )
    stats = innings.groupby("venue", as_index=False).agg(
        matches=("match_id", "nunique"),
        avg_innings_score=("runs", "mean"),
        highest_innings=("runs", "max"),
        avg_wickets_per_innings=("wickets", "mean"),
    )
    stats["avg_innings_score"] = stats["avg_innings_score"].round(1)
    stats["avg_wickets_per_innings"] = stats["avg_wickets_per_innings"].round(1)
    return stats.sort_values("matches", ascending=False)


def head_to_head(results: pd.DataFrame, team: str) -> pd.DataFrame:
    """Win/loss record of `team` against each opponent it has faced."""
    decided = results.dropna(subset=["winner"])
    matches = decided[(decided["team1"] == team) | (decided["team2"] == team)]
    opponents = pd.unique(matches[["team1", "team2"]].values.ravel())

    rows = []
    for opp in opponents:
        if opp == team or pd.isna(opp):
            continue
        sub = matches[(matches["team1"] == opp) | (matches["team2"] == opp)]
        played = len(sub)
        wins = int((sub["winner"] == team).sum())
        losses = int((sub["winner"] == opp).sum())
        rows.append(
            {
                "opponent": opp,
                "played": played,
                "wins": wins,
                "losses": losses,
                "win_pct": round(wins / played * 100, 1) if played else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values("played", ascending=False)


def run_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["total_runs"].value_counts().sort_index().reset_index()
    counts.columns = ["runs", "deliveries"]
    legal = df.loc[df["is_legal_delivery"] == 1]
    total_legal = len(legal)
    counts["share_pct"] = (counts["deliveries"] / total_legal * 100).round(1)
    return counts
