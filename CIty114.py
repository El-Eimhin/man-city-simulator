import json
import warnings

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


warnings.filterwarnings("ignore")


# -------------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------------

st.set_page_config(
    page_title="Manchester City Removal Simulator",
    page_icon="⚽",
    layout="wide",
)


# -------------------------------------------------------------------------
# APP STYLING
# -------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1250px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, h4 {
            letter-spacing: -0.02em;
        }

        .app-subtitle {
            max-width: 850px;
            color: #475569;
            font-size: 1.05rem;
            line-height: 1.7;
            margin-bottom: 1.5rem;
        }

        .method-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #1e3a8a;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }

        .method-title {
            color: #0f172a;
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .method-text {
            color: #475569;
            line-height: 1.6;
            margin: 0;
        }

        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
        }

        div[data-testid="stSelectbox"] label {
            color: #334155;
            font-weight: 600;
        }

        div[data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin-bottom: 0.8rem;
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            color: #0f172a;
            font-weight: 700;
        }

        .section-note {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.6;
            margin-top: -0.5rem;
            margin-bottom: 1.25rem;
        }

        .mover-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            min-height: 155px;
            padding: 1.2rem 1.3rem;
        }

        .mover-card-gain {
            border-top: 4px solid #16a34a;
        }

        .mover-card-loss {
            border-top: 4px solid #dc2626;
        }

        .mover-label {
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }

        .mover-team {
            color: #0f172a;
            font-size: 1.25rem;
            font-weight: 750;
            line-height: 1.3;
            margin-bottom: 0.45rem;
        }

        .mover-detail {
            color: #475569;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .mover-positive {
            color: #15803d;
            font-weight: 700;
        }

        .mover-negative {
            color: #b91c1c;
            font-weight: 700;
        }

        .footer-note {
            color: #64748b;
            font-size: 0.85rem;
            line-height: 1.5;
            margin-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------------
# PAGE INTRODUCTION
# -------------------------------------------------------------------------

st.title("Manchester City Removal Simulator")

st.markdown(
    """
    <div class="app-subtitle">
        A Premier League counterfactual showing what each final league table
        would look like if every Manchester City fixture were removed from
        the season.
    </div>

    <div class="method-box">
        <div class="method-title">How it works</div>
        <p class="method-text">
            Matches involving Manchester City are excluded and the standings
            are rebuilt using the remaining results. Some clubs move up after
            heavy defeats disappear, while others move down because points
            earned against City are removed.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------------

CITY_NAME = "Man City"

SEASONS = {
    "2009/10": "0910",
    "2010/11": "1011",
    "2011/12": "1112",
    "2012/13": "1213",
    "2013/14": "1314",
    "2014/15": "1415",
    "2015/16": "1516",
    "2016/17": "1617",
    "2017/18": "1718",
}


# -------------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------------

def ordinal(number):
    """Convert an integer into an ordinal string."""

    number = int(number)

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(number % 10, "th")

    return f"{number}{suffix}"


def format_team_list(teams):
    """Convert a list of team names into readable text."""

    teams = list(teams)

    if not teams:
        return ""

    if len(teams) == 1:
        return teams[0]

    if len(teams) == 2:
        return f"{teams[0]} and {teams[1]}"

    return ", ".join(teams[:-1]) + f", and {teams[-1]}"


def style_change(value):
    """Apply formatting to positive and negative changes."""

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return ""

    if numeric_value > 0:
        return (
            "color: #15803d; "
            "background-color: #f0fdf4; "
            "font-weight: 600;"
        )

    if numeric_value < 0:
        return (
            "color: #b91c1c; "
            "background-color: #fef2f2; "
            "font-weight: 600;"
        )

    return "color: #64748b;"


# -------------------------------------------------------------------------
# DATA FUNCTIONS
# -------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_data(season_code):
    """Load Premier League match data for a selected season."""

    url = (
        "https://www.football-data.co.uk/mmz4281/"
        f"{season_code}/E0.csv"
    )

    required_columns = {
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
    }

    try:
        df = pd.read_csv(
            url,
            on_bad_lines="skip",
        )

    except Exception as exc:
        raise RuntimeError(
            f"Could not load match data for season {season_code}."
        ) from exc

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))

        raise ValueError(
            f"The source data is missing required columns: {missing}"
        )

    df = df.dropna(
        subset=[
            "HomeTeam",
            "AwayTeam",
            "FTHG",
            "FTAG",
        ]
    ).copy()

    df["FTHG"] = pd.to_numeric(
        df["FTHG"],
        errors="coerce",
    )

    df["FTAG"] = pd.to_numeric(
        df["FTAG"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "FTHG",
            "FTAG",
        ]
    ).copy()

    df["FTHG"] = df["FTHG"].astype(int)
    df["FTAG"] = df["FTAG"].astype(int)

    return df


def build_league_table(df):
    """Build a league table from a collection of match results."""

    teams = sorted(
        set(df["HomeTeam"]).union(
            set(df["AwayTeam"])
        )
    )

    table = {
        team: {
            "P": 0,
            "W": 0,
            "D": 0,
            "L": 0,
            "GF": 0,
            "GA": 0,
            "Pts": 0,
        }
        for team in teams
    }

    for row in df.itertuples(index=False):
        home_team = row.HomeTeam
        away_team = row.AwayTeam
        home_goals = int(row.FTHG)
        away_goals = int(row.FTAG)

        table[home_team]["P"] += 1
        table[home_team]["GF"] += home_goals
        table[home_team]["GA"] += away_goals

        table[away_team]["P"] += 1
        table[away_team]["GF"] += away_goals
        table[away_team]["GA"] += home_goals

        if home_goals > away_goals:
            table[home_team]["W"] += 1
            table[home_team]["Pts"] += 3
            table[away_team]["L"] += 1

        elif away_goals > home_goals:
            table[away_team]["W"] += 1
            table[away_team]["Pts"] += 3
            table[home_team]["L"] += 1

        else:
            table[home_team]["D"] += 1
            table[away_team]["D"] += 1
            table[home_team]["Pts"] += 1
            table[away_team]["Pts"] += 1

    standings = pd.DataFrame.from_dict(
        table,
        orient="index",
    )

    standings["GD"] = (
        standings["GF"] - standings["GA"]
    )

    standings = standings.sort_values(
        by=[
            "Pts",
            "GD",
            "GF",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    standings = standings.reset_index()

    standings = standings.rename(
        columns={
            "index": "Team",
        }
    )

    standings.index = standings.index + 1
    standings.index.name = "Position"

    return standings


def remove_city_fixtures(df):
    """Exclude every match involving Manchester City."""

    return df[
        (df["HomeTeam"] != CITY_NAME)
        & (df["AwayTeam"] != CITY_NAME)
    ].copy()


def compare_tables(original_table, recalculated_table):
    """Compare original and recalculated league positions."""

    comparison = recalculated_table.copy()

    original_ranks = {
        row["Team"]: position
        for position, row in original_table.iterrows()
    }

    original_points = {
        row["Team"]: row["Pts"]
        for _, row in original_table.iterrows()
    }

    original_goal_difference = {
        row["Team"]: row["GD"]
        for _, row in original_table.iterrows()
    }

    comparison["Orig_Rank"] = comparison["Team"].map(
        original_ranks
    )

    comparison["Orig_Pts"] = comparison["Team"].map(
        original_points
    )

    comparison["Pos_Change"] = (
        comparison["Orig_Rank"]
        - comparison.index
    )

    comparison["Pts_Change"] = (
        comparison["Pts"]
        - comparison["Orig_Pts"]
    )

    comparison["GD_Change"] = (
        comparison["GD"]
        - comparison["Team"].map(
            original_goal_difference
        )
    )

    integer_columns = [
        "Orig_Rank",
        "Orig_Pts",
        "Pos_Change",
        "Pts_Change",
        "GD_Change",
    ]

    comparison[integer_columns] = comparison[
        integer_columns
    ].astype(int)

    return comparison


@st.cache_data(show_spinner=False)
def get_all_time_stats():
    """Calculate aggregate point changes across all seasons."""

    aggregate_changes = {}

    for season_code in SEASONS.values():
        season_df = load_data(season_code)

        original_table = build_league_table(
            season_df
        )

        recalculated_table = build_league_table(
            remove_city_fixtures(season_df)
        )

        original_points = {
            row["Team"]: row["Pts"]
            for _, row in original_table.iterrows()
        }

        for _, row in recalculated_table.iterrows():
            team = row["Team"]

            points_change = (
                int(row["Pts"])
                - int(original_points[team])
            )

            aggregate_changes[team] = (
                aggregate_changes.get(team, 0)
                + points_change
            )

    all_time_df = pd.DataFrame.from_dict(
        aggregate_changes,
        orient="index",
        columns=["Points change"],
    )

    all_time_df.index.name = "Team"

    all_time_df = all_time_df[
        all_time_df.index != CITY_NAME
    ]

    all_time_df = all_time_df.sort_values(
        by="Points change",
        ascending=True,
    )

    return all_time_df


# -------------------------------------------------------------------------
# 1. SEASON SELECTOR
# -------------------------------------------------------------------------

st.subheader("Season selector")

st.markdown(
    """
    <div class="section-note">
        Select a Premier League season to recalculate. Every section below
        updates automatically when a different season is chosen.
    </div>
    """,
    unsafe_allow_html=True,
)

selected_season = st.selectbox(
    "Select a season",
    options=list(SEASONS.keys()),
    index=0,
)

season_code = SEASONS[selected_season]


# -------------------------------------------------------------------------
# SEASON CALCULATIONS
# -------------------------------------------------------------------------

try:
    with st.spinner("Loading match results..."):
        match_data = load_data(season_code)

except Exception as exc:
    st.error(
        "The match data could not be loaded. "
        "Please check the source connection and try again."
    )

    st.exception(exc)
    st.stop()


original_table = build_league_table(
    match_data
)

matches_without_city = remove_city_fixtures(
    match_data
)

recalculated_table = build_league_table(
    matches_without_city
)

comparison = compare_tables(
    original_table,
    recalculated_table,
)

original_champion = original_table.iloc[0]["Team"]
recalculated_champion = comparison.iloc[0]["Team"]


# -------------------------------------------------------------------------
# PREPARE ANIMATION DATA
# -------------------------------------------------------------------------

animation_data = []

for original_position, row in original_table.iterrows():
    team = row["Team"]

    if team == CITY_NAME:
        animation_data.append(
            {
                "team": team,
                "orig_rank": int(original_position),
                "orig_pts": int(row["Pts"]),
                "new_rank": len(original_table) + 1,
                "new_pts": 0,
                "pos_change": 0,
                "pts_change": 0,
            }
        )

        continue

    new_row = comparison[
        comparison["Team"] == team
    ].iloc[0]

    animation_data.append(
        {
            "team": team,
            "orig_rank": int(original_position),
            "orig_pts": int(row["Pts"]),
            "new_rank": int(new_row.name),
            "new_pts": int(new_row["Pts"]),
            "pos_change": int(new_row["Pos_Change"]),
            "pts_change": int(new_row["Pts_Change"]),
        }
    )


animation_json = json.dumps(
    animation_data
)


# -------------------------------------------------------------------------
# 2. ANIMATED LEAGUE TABLE
# -------------------------------------------------------------------------

st.divider()
st.subheader("Animated league table")

st.markdown(
    f"""
    <div class="section-note">
        The table begins with the original {selected_season} final standings.
        Select <strong>Recalculate standings</strong> to remove Manchester
        City and reorder the remaining clubs.
    </div>
    """,
    unsafe_allow_html=True,
)


html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            background: transparent;
            color: #0f172a;
            font-family: Inter, "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 2px;
        }}

        .controls {{
            align-items: center;
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 18px;
        }}

        button {{
            background: #0f172a;
            border: 1px solid #0f172a;
            border-radius: 7px;
            color: #ffffff;
            cursor: pointer;
            font-size: 15px;
            font-weight: 650;
            padding: 11px 20px;
            transition:
                background 0.2s ease,
                border-color 0.2s ease,
                transform 0.2s ease;
        }}

        button:hover {{
            background: #1e3a8a;
            border-color: #1e3a8a;
            transform: translateY(-1px);
        }}

        button:disabled {{
            cursor: default;
            opacity: 0.55;
            transform: none;
        }}

        .reset-button {{
            background: #ffffff;
            border-color: #cbd5e1;
            color: #334155;
        }}

        .reset-button:hover {{
            background: #f8fafc;
            border-color: #94a3b8;
        }}

        .board-container {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin: 0 auto;
            max-width: 780px;
            overflow: hidden;
        }}

        .header-row {{
            align-items: center;
            background: #0f172a;
            color: #ffffff;
            display: flex;
            font-size: 12px;
            font-weight: 700;
            height: 42px;
            letter-spacing: 0.04em;
            padding: 0 10px;
            text-transform: uppercase;
        }}

        .board {{
            height: 890px;
            padding: 10px;
            position: relative;
            width: 100%;
        }}

        .team-row {{
            align-items: center;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            display: flex;
            height: 39px;
            left: 10px;
            position: absolute;
            transition:
                top 1.25s cubic-bezier(0.4, 0, 0.2, 1),
                opacity 0.6s ease,
                transform 0.6s ease,
                background-color 0.8s ease,
                border-color 0.8s ease;
            width: calc(100% - 20px);
        }}

        .team-row:hover {{
            border-color: #94a3b8;
        }}

        .rank-column {{
            color: #475569;
            font-size: 15px;
            font-weight: 700;
            text-align: center;
            width: 64px;
        }}

        .team-column {{
            color: #0f172a;
            flex-grow: 1;
            font-size: 15px;
            font-weight: 650;
            padding-left: 4px;
        }}

        .change-column {{
            color: #64748b;
            font-size: 13px;
            font-weight: 650;
            opacity: 0;
            text-align: center;
            transition: opacity 0.8s ease;
            width: 120px;
        }}

        .points-column {{
            color: #0f172a;
            font-size: 15px;
            font-weight: 750;
            padding-right: 18px;
            text-align: right;
            width: 85px;
        }}

        .rank-header {{
            text-align: center;
            width: 64px;
        }}

        .team-header {{
            flex-grow: 1;
            padding-left: 4px;
        }}

        .change-header {{
            text-align: center;
            width: 120px;
        }}

        .points-header {{
            padding-right: 18px;
            text-align: right;
            width: 85px;
        }}

        .moves-up {{
            background: #f0fdf4;
            border-color: #86efac;
        }}

        .moves-down {{
            background: #fef2f2;
            border-color: #fca5a5;
        }}

        .unchanged {{
            background: #f8fafc;
        }}

        .city-row {{
            background: #eff6ff;
            border-color: #93c5fd;
        }}

        .removed {{
            opacity: 0;
            pointer-events: none;
            transform: translateX(25px);
        }}

        .negative {{
            color: #b91c1c;
        }}

        .neutral {{
            color: #64748b;
        }}

        @media (max-width: 650px) {{
            .change-column,
            .change-header {{
                width: 90px;
            }}

            .team-column {{
                font-size: 13px;
            }}

            .rank-column,
            .rank-header {{
                width: 48px;
            }}
        }}
    </style>
</head>

<body>
    <div class="controls">
        <button
            id="apply-button"
            type="button"
            onclick="animateTable()"
        >
            Recalculate standings
        </button>

        <button
            class="reset-button"
            id="reset-button"
            type="button"
            onclick="resetTable()"
        >
            Reset
        </button>
    </div>

    <div class="board-container">
        <div class="header-row">
            <div class="rank-header">Pos.</div>
            <div class="team-header">Club</div>
            <div class="change-header">Points change</div>
            <div class="points-header">Pts</div>
        </div>

        <div class="board" id="board"></div>
    </div>

    <script>
        const data = {animation_json};
        const board = document.getElementById("board");

        const applyButton = document.getElementById(
            "apply-button"
        );

        function cleanID(name) {{
            return name.replace(
                /[^a-zA-Z0-9]/g,
                "-"
            );
        }}

        function formatPointsChange(value) {{
            if (value > 0) {{
                return "+" + value;
            }}

            return String(value);
        }}

        function renderInitialTable() {{
            board.innerHTML = "";

            data.forEach((item) => {{
                const row = document.createElement("div");
                const teamID = cleanID(item.team);

                row.className = "team-row";

                if (item.team === "{CITY_NAME}") {{
                    row.classList.add("city-row");
                }}

                row.id = "team-" + teamID;

                row.style.top =
                    ((item.orig_rank - 1) * 44) + "px";

                row.innerHTML = `
                    <div class="rank-column">
                        ${{item.orig_rank}}
                    </div>

                    <div class="team-column">
                        ${{item.team}}
                    </div>

                    <div
                        class="change-column"
                        id="change-${{teamID}}"
                    >
                        ${{formatPointsChange(item.pts_change)}}
                    </div>

                    <div
                        class="points-column"
                        id="points-${{teamID}}"
                    >
                        ${{item.orig_pts}}
                    </div>
                `;

                board.appendChild(row);
            }});
        }}

        function animateTable() {{
            applyButton.disabled = true;

            const cityRow = document.getElementById(
                "team-" + cleanID("{CITY_NAME}")
            );

            if (cityRow) {{
                cityRow.classList.add("removed");
            }}

            setTimeout(() => {{
                data.forEach((item) => {{
                    if (item.team === "{CITY_NAME}") {{
                        return;
                    }}

                    const teamID = cleanID(item.team);

                    const row = document.getElementById(
                        "team-" + teamID
                    );

                    if (!row) {{
                        return;
                    }}

                    const rankCell = row.querySelector(
                        ".rank-column"
                    );

                    const pointsCell = document.getElementById(
                        "points-" + teamID
                    );

                    const changeCell = document.getElementById(
                        "change-" + teamID
                    );

                    row.style.top =
                        ((item.new_rank - 1) * 44) + "px";

                    rankCell.innerText = item.new_rank;
                    pointsCell.innerText = item.new_pts;

                    changeCell.innerText = formatPointsChange(
                        item.pts_change
                    );

                    changeCell.style.opacity = "1";

                    changeCell.classList.remove(
                        "negative",
                        "neutral"
                    );

                    if (item.pts_change < 0) {{
                        changeCell.classList.add("negative");
                    }} else {{
                        changeCell.classList.add("neutral");
                    }}

                    row.classList.remove(
                        "moves-up",
                        "moves-down",
                        "unchanged"
                    );

                    if (item.pos_change > 0) {{
                        row.classList.add("moves-up");

                    }} else if (item.pos_change < 0) {{
                        row.classList.add("moves-down");

                    }} else {{
                        row.classList.add("unchanged");
                    }}
                }});
            }}, 350);
        }}

        function resetTable() {{
            applyButton.disabled = false;
            renderInitialTable();
        }}

        renderInitialTable();
    </script>
</body>
</html>
"""


components.html(
    html_code,
    height=1020,
    scrolling=False,
)


# -------------------------------------------------------------------------
# 3. RECALCULATED LEAGUE TABLE
# -------------------------------------------------------------------------

st.divider()
st.subheader("Recalculated league table")

st.markdown(
    """
    <div class="section-note">
        Position change compares each club's original finishing position
        with its position after Manchester City fixtures are removed.
        A positive value indicates that the club moves up.
    </div>
    """,
    unsafe_allow_html=True,
)


display_columns = [
    "Team",
    "P",
    "W",
    "D",
    "L",
    "GF",
    "GA",
    "GD",
    "Pts",
    "Pts_Change",
    "Orig_Rank",
    "Pos_Change",
]

comparison_display = comparison[
    display_columns
].copy()

comparison_display = comparison_display.rename(
    columns={
        "P": "Played",
        "W": "Won",
        "D": "Drawn",
        "L": "Lost",
        "Pts": "Points",
        "Pts_Change": "Points Change",
        "Orig_Rank": "Original Position",
        "Pos_Change": "Position Change",
    }
)


styled_table = (
    comparison_display.style
    .map(
        style_change,
        subset=[
            "Position Change",
            "Points Change",
        ],
    )
    .format(
        {
            "Points": "{:.0f}",
            "Points Change": "{:+.0f}",
            "Position Change": "{:+.0f}",
            "Original Position": "{:.0f}",
        }
    )
)


st.dataframe(
    styled_table,
    height=720,
    use_container_width=True,
    hide_index=False,
)


# -------------------------------------------------------------------------
# CALCULATE FINDINGS
# -------------------------------------------------------------------------

biggest_gd_winner = comparison.loc[
    comparison["GD_Change"].idxmax()
]

largest_gain = int(
    comparison["Pos_Change"].max()
)

largest_loss = int(
    comparison["Pos_Change"].min()
)


if largest_gain > 0:
    biggest_gainers = comparison[
        comparison["Pos_Change"] == largest_gain
    ].copy()

    biggest_gainer_names = format_team_list(
        biggest_gainers["Team"].tolist()
    )

    gainer_movements = []

    for new_position, row in biggest_gainers.iterrows():
        gainer_movements.append(
            f"{row['Team']}: "
            f"{ordinal(row['Orig_Rank'])} to "
            f"{ordinal(new_position)}"
        )

    gainer_position_text = "<br>".join(
        gainer_movements
    )

else:
    biggest_gainers = pd.DataFrame()
    biggest_gainer_names = "No upward movement"

    gainer_position_text = (
        "No club moves above its original position."
    )


if largest_loss < 0:
    biggest_losers = comparison[
        comparison["Pos_Change"] == largest_loss
    ].copy()

    biggest_loser_names = format_team_list(
        biggest_losers["Team"].tolist()
    )

    loser_movements = []

    for new_position, row in biggest_losers.iterrows():
        loser_movements.append(
            f"{row['Team']}: "
            f"{ordinal(row['Orig_Rank'])} to "
            f"{ordinal(new_position)}"
        )

    loser_position_text = "<br>".join(
        loser_movements
    )

else:
    biggest_losers = pd.DataFrame()
    biggest_loser_names = "No downward movement"

    loser_position_text = (
        "No club falls below its original position."
    )


original_top_four = set(
    original_table.head(4)["Team"]
)

recalculated_top_four = set(
    comparison.head(4)["Team"]
)

original_relegation_places = set(
    original_table.tail(3)["Team"]
)

# The simulated table contains 19 clubs, so the bottom two
# are treated as the equivalent relegation positions.
recalculated_relegation_places = set(
    comparison.tail(2)["Team"]
)

falls_out = (
    original_top_four
    - recalculated_top_four
    - {CITY_NAME}
)

moves_in = (
    recalculated_top_four
    - original_top_four
)

avoids_relegation = (
    original_relegation_places
    - recalculated_relegation_places
    - {CITY_NAME}
)

drops_into_relegation = (
    recalculated_relegation_places
    - original_relegation_places
)


# -------------------------------------------------------------------------
# 4. COLLAPSIBLE ANALYSIS SECTIONS
# -------------------------------------------------------------------------

st.divider()
st.subheader("Season analysis")

st.markdown(
    """
    <div class="section-note">
        Expand the sections below to examine the main consequences of
        removing Manchester City's fixtures.
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------------
# 4A. KEY FINDINGS
# -------------------------------------------------------------------------

with st.expander(
    "Key findings",
    expanded=False,
):
    champion_column, goal_difference_column = st.columns(
        2,
        gap="large",
    )

    with champion_column:
        st.markdown("#### League winner")

        if original_champion == CITY_NAME:
            st.success(
                f"Manchester City finished first in the original "
                f"{selected_season} table. After City fixtures are "
                f"removed, **{recalculated_champion}** finishes top."
            )

        elif original_champion != recalculated_champion:
            st.warning(
                f"**{original_champion}** won the original league, "
                f"but **{recalculated_champion}** moves into first "
                f"in the recalculated standings."
            )

        else:
            st.info(
                f"Removing City fixtures does not change the winner. "
                f"**{original_champion}** remains first."
            )

    with goal_difference_column:
        st.markdown("#### Goal-difference impact")

        gd_change = int(
            biggest_gd_winner["GD_Change"]
        )

        gd_prefix = "+" if gd_change > 0 else ""

        st.info(
            f"**{biggest_gd_winner['Team']}** records the largest "
            f"improvement in goal difference, changing by "
            f"**{gd_prefix}{gd_change}** after City fixtures "
            f"are removed."
        )



# -------------------------------------------------------------------------
# 4C. EUROPEAN QUALIFICATION AND RELEGATION
# -------------------------------------------------------------------------

with st.expander(
    "European qualification and relegation changes",
    expanded=False,
):
    st.markdown(
        """
        <div class="section-note">
            This section compares the European qualification and relegation
            positions in the original and recalculated tables.
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_four_column, relegation_column = st.columns(
        2,
        gap="large",
    )

    with top_four_column:
        st.markdown("#### European places")

        if falls_out:
            st.error(
                "**Falls out of the top four:** "
                + ", ".join(sorted(falls_out))
            )

        if moves_in:
            st.success(
                "**Moves into the top four:** "
                + ", ".join(sorted(moves_in))
            )

        if not falls_out and not moves_in:
            st.info(
                "The composition of the top four does not change."
            )

        st.caption(
            "This is a mathematical comparison only and does not "
            "attempt to recreate historical UEFA qualification rules."
        )

    with relegation_column:
        st.markdown("#### Relegation places")

        if avoids_relegation:
            st.success(
                "**Moves out of the relegation places:** "
                + ", ".join(sorted(avoids_relegation))
            )

        if drops_into_relegation:
            st.error(
                "**Drops into the relegation places:** "
                + ", ".join(sorted(drops_into_relegation))
            )

        if (
            not avoids_relegation
            and not drops_into_relegation
        ):
            st.info(
                "Removing City fixtures does not change the "
                "relegation picture."
            )

        st.caption(
            "Because the simulated league contains 19 clubs, the "
            "bottom two positions are treated as the relegation places."
        )



# -------------------------------------------------------------------------
# METHODOLOGY NOTE
# -------------------------------------------------------------------------

st.markdown(
    """
    <div class="footer-note">
        <strong>Methodology note:</strong> This simulation removes every
        Manchester City fixture and recalculates points, goals scored,
        goals conceded and goal difference from the remaining matches.
        It does not account for behavioural changes, fixture sequencing,
        historical competition rules or other consequences that might
        arise in a genuine 19-team league.
    </div>
    """,
    unsafe_allow_html=True,
)
