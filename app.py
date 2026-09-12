import os
import pandas as pd
from dash import Dash, dcc, html, Output, Input, State, ALL, ctx
import plotly.express as px

# ============================================================
# CONFIG
# ============================================================

port = int(os.environ.get("PORT", 8050))

competition_order = [
    "IROS 2024",
    "CDC 2024",
    "ICRA 2025",
    "CDC-TF 2025",
    "ICRA 2026",
    "IROS 2026",
]

competition_labels = {
    "All Competitions": "All Competitions",
    "IROS 2024": "IROS 2024",
    "CDC 2024": "CDC 2024",
    "ICRA 2025": "ICRA 2025",
    "CDC-TF 2025": "CDC-TF 2025",
    "ICRA 2026": "ICRA 2026",
    "IROS 2026": "IROS 2026",
}

metric_labels = {
    "Teams": "Number of Teams",
    "Participants": "Number of Participants",
    "Organizations": "Number of Organizations",
    "Participation": "Number of Competitions",
}


# ============================================================
# LOAD AND CLEAN DATA
# ============================================================

def load_competition(sheet_name):

    df = pd.read_excel(
        "https://raw.githubusercontent.com/AutoDRIVE-Ecosystem/AutoDRIVE-RoboRacer-Sim-Racing-Participation/main/Registration.xlsx",
        sheet_name=sheet_name,
        header=None,
    )

    df.columns = [
        "SR NO",
        "TEAM NAME",
        "TEAM MEMBER",
        "ORGANIZATION",
        "COUNTRY",
    ]

    fill_cols = [
        "SR NO",
        "TEAM NAME",
        "ORGANIZATION",
        "COUNTRY",
    ]

    df[fill_cols] = df[fill_cols].ffill()

    df = df.dropna(
        subset=["TEAM MEMBER"]
    )

    df["Competition"] = sheet_name

    return df


all_data = pd.concat(
    [
        load_competition(c)
        for c in competition_order
    ],
    ignore_index=True,
)


# ============================================================
# COUNTRY NORMALIZATION
# ============================================================

country_alias_map = {
    "USA": "United States",
    "U.S.": "United States",
    "United States of America (USA)": "United States",
    "United States (US)": "United States",
    "UAE": "United Arab Emirates",
    "United Arab Emirates (UAE)": "United Arab Emirates",
    "Côte d'Ivoire": "Ivory Coast",
    "Republic of Korea": "South Korea",
    "Republic of Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "Türkiye": "Turkey",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
}

df_split = all_data.copy()

df_split["COUNTRY"] = (
    df_split["COUNTRY"]
    .astype(str)
    .str.replace(
        r"\s*&\s*|\s*/\s*|\s+and\s+",
        ",",
        regex=True,
    )
)

df_split["COUNTRY"] = (
    df_split["COUNTRY"]
    .str.split(",")
)

df_split = df_split.explode(
    "COUNTRY"
)

df_split["COUNTRY"] = (
    df_split["COUNTRY"]
    .str.strip()
)

df_split["COUNTRY"] = (
    df_split["COUNTRY"]
    .replace(country_alias_map)
)

# ============================================================
# AGGREGATE DATA
# ============================================================

per_competition = (
    df_split
    .groupby(
        [
            "Competition",
            "COUNTRY",
        ]
    )
    .agg(
        Teams=(
            "TEAM NAME",
            "nunique",
        ),
        Participants=(
            "TEAM MEMBER",
            "count",
        ),
        Organizations=(
            "ORGANIZATION",
            "nunique",
        ),
    )
    .reset_index()
)

all_combined = (
    df_split
    .groupby("COUNTRY")
    .agg(
        Teams=(
            "TEAM NAME",
            "nunique",
        ),
        Participants=(
            "TEAM MEMBER",
            "count",
        ),
        Organizations=(
            "ORGANIZATION",
            "nunique",
        ),
        Participation=(
            "Competition",
            "nunique",
        ),
    )
    .reset_index()
)

all_combined["Competition"] = (
    "All Competitions"
)

map_data = pd.concat(
    [
        per_competition,
        all_combined,
    ],
    ignore_index=True,
)

# ============================================================
# DROPDOWN OPTIONS
# ============================================================

competition_options = [
    {
        "label": c,
        "value": c,
    }
    for c in (
        ["All Competitions"]
        + competition_order
    )
]

def get_metric_options(selected_competition):

    metrics = [
        "Teams",
        "Participants",
        "Organizations",
    ]

    if selected_competition == "All Competitions":
        metrics.append("Participation")

    return [
        {
            "label": metric_labels[m],
            "value": m,
        }
        for m in metrics
    ]

# ============================================================
# CUSTOM RACING DROPDOWN
# ============================================================

def racing_dropdown(
    dropdown_id,
    options,
    value,
):

    return html.Div(

        id={
            "type": "racing-dropdown",
            "id": dropdown_id,
        },

        className="racing-dropdown",

        children=[

            html.Button(

                id={
                    "type":
                        "racing-dropdown-button",
                    "id":
                        dropdown_id,
                },

                className=
                    "racing-dropdown-button",

                n_clicks=0,

                children=[

                    html.Span(

                        (
                            competition_labels.get(
                                value,
                                value,
                            )
                            if dropdown_id
                            == "competition-select"
                            else metric_labels.get(
                                value,
                                value,
                            )
                        ),

                        id={
                            "type":
                                "racing-dropdown-value",
                            "id":
                                dropdown_id,
                        },
                    ),

                    html.Span(
                        className=
                            "racing-dropdown-chevron"
                    ),
                ],
            ),

            html.Div(

                id={
                    "type":
                        "racing-dropdown-menu",
                    "id":
                        dropdown_id,
                },

                className=
                    "racing-dropdown-menu",

                children=[

                    html.Button(

                        option["label"],

                        id={
                            "type":
                                "racing-dropdown-option",

                            "dropdown":
                                dropdown_id,

                            "value":
                                option["value"],
                        },

                        className=(
                            "racing-dropdown-option"
                            +
                            (
                                " selected"
                                if option["value"]
                                == value
                                else ""
                            )
                        ),

                        n_clicks=0,

                    )

                    for option in options
                ],
            ),

            dcc.Store(

                id={
                    "type":
                        "racing-dropdown-store",
                    "id":
                        dropdown_id,
                },

                data=value,
            ),
        ],
    )


# ============================================================
# DASH APP
# ============================================================

app = Dash(__name__)

app.title = (
    "AutoDRIVE-RoboRacer Sim Racing"
)

# ============================================================
# CUSTOM HTML / CSS / JS
# ============================================================

app.index_string = """

<!DOCTYPE html>

<html>

<head>

    {%metas%}

    <title>{%title%}</title>

    <link
        rel="icon"
        type="image/png"
        href="/assets/favicon.png"
    >

    {%css%}

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <link
        rel="preconnect"
        href="https://fonts.googleapis.com"
    >

    <link
        rel="preconnect"
        href="https://fonts.gstatic.com"
        crossorigin
    >

    <link
        href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap"
        rel="stylesheet"
    >

    <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,500,0,0"
        rel="stylesheet"
    >

<style>

/* ============================================================
   GLOBAL
   ============================================================ */

* {
    box-sizing: border-box;
}

html,
body {

    margin: 0;
    padding: 0;

    min-height: 100%;

    background: #050505 !important;

    color: #ffffff;

    font-family:
        "Inter",
        Arial,
        sans-serif;
}

body {
    overflow-x: hidden;
}

/* ============================================================
   APP
   ============================================================ */

.race-app {

    min-height: 100vh;

    padding:
        0 28px 40px;

    background:

        radial-gradient(
            ellipse at 50% -20%,
            rgba(225, 6, 0, 0.13),
            transparent 45%
        ),

        linear-gradient(
            180deg,
            #090909 0%,
            #050505 100%
        );
}

.race-container {

    width: 100%;

    max-width: 1600px;

    margin: 0 auto;
}

.race-stripe {

    height: 5px;

    background:

        linear-gradient(
            90deg,
            transparent,
            #e10600 18%,
            #ff3027 50%,
            #e10600 82%,
            transparent
        );

    box-shadow:
        0 0 25px
        rgba(225,6,0,0.55);
}

/* ============================================================
   HEADER
   ============================================================ */

.topbar {

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding:
        20px 2px 17px;

    border-bottom:
        1px solid
        rgba(255,255,255,0.07);
}

.brand {

    display: flex;

    align-items: center;

    gap: 15px;
}

/* ============================================================
   HEADER CHECKERED FLAG
   ============================================================ */

.checker-flag {
    width: 58px;
    height: 58px;
    flex: 0 0 58px;
    position: relative;
    overflow: hidden;
    border: 1px solid #333333;
    box-shadow: 0 0 25px rgba(225, 6, 0, 0.20);
    transform: skew(-7deg);
    background-color: #ffffff;

    background-image:
        linear-gradient(
            45deg,
            #050505 25%,
            transparent 25%,
            transparent 75%,
            #050505 75%
        ),
        linear-gradient(
            45deg,
            #050505 25%,
            transparent 25%,
            transparent 75%,
            #050505 75%
        );

    background-position:
        0 0,
        10px 10px;

    background-size:
        20px 20px;
}

.checker-flag::after {
    content: "";
    position: absolute;
    inset: 0;

    background:
        linear-gradient(
            135deg,
            rgba(225, 6, 0, 0.0) 50%,
            rgba(225, 6, 0, 0.55) 100%
        );

    pointer-events: none;
}

/* ============================================================
   BRAND
   ============================================================ */

.series-title {

    margin: 0;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size: 30px;

    line-height: 0.9;

    font-weight: 900;

    letter-spacing: 1px;

    text-transform: uppercase;
}

.series-subtitle {

    margin-top: 7px;

    color: #686868;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 2px;

    text-transform: uppercase;
}

.series-subtitle span {
    color: #e10600;
}

.header-right {

    display: flex;

    align-items: center;

    gap: 17px;
}

.live-dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 10px
        rgba(34,197,94,0.8);
}

.hub-link {

    display: flex;

    align-items: center;

    justify-content: center;

    height: 42px;

    padding:
        0 18px;

    border:
        1px solid #303030;

    background:
        #0d0d0d;

    color:
        #ffffff;

    text-decoration: none;

    font-size: 9px;

    font-weight: 800;

    letter-spacing: 1.2px;

    transition: 0.2s ease;
}

.hub-link:hover {

    border-color:
        #e10600;

    background:
        #e10600;

    box-shadow:
        0 0 20px
        rgba(225,6,0,0.3);
}

.material-symbols-outlined {

    font-size: 15px;

    line-height: 1;

    margin-left: 7px;

    font-variation-settings:
        "FILL" 0,
        "wght" 500,
        "GRAD" 0,
        "opsz" 20;
}

/* ============================================================
   HERO
   ============================================================ */

.hero {

    position: relative;

    padding:
        34px 0 24px;

    overflow: hidden;
}

.hero-content {

    position: relative;

    z-index: 2;
}


/* ============================================================
   HERO — LARGE TRANSLUCENT CHECKERED FLAG
   ============================================================ */

.flag {
    position: absolute;

    right: -20px;
    top: 50%;

    width: 300px;
    height: 150px;

    opacity: 0.10;

    pointer-events: none;

    background:
        conic-gradient(
            #ffffff 25%,
            transparent 0 50%,
            #ffffff 0 75%,
            transparent 0
        );

    background-size: 40px 40px;

    transform:
        translateY(-50%)
        skew(-15deg)
        perspective(500px)
        rotateY(-20deg);

    transform-origin: center;

    z-index: 0;
}

.hero-kicker {

    margin-bottom: 5px;

    color:
        #858585;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size: 13px;

    font-weight: 800;

    letter-spacing: 3px;

    text-transform: uppercase;
}

.hero-kicker span {
    color: #e10600;
}

.hero-title {

    margin: 0;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size:
        clamp(48px, 6vw, 80px);

    line-height: 0.83;

    font-weight: 900;

    letter-spacing: -1px;

    text-transform: uppercase;
}

.hero-title .red {
    color: #e10600;
}

.hero-description {

    margin-top: 14px;

    max-width: 600px;

    color: #696969;

    font-size: 11px;

    line-height: 1.55;
}

/* ============================================================
   CHECKERBOARD CONTROL STRIP
   ============================================================ */

.flag-control-zone {

    position: relative;

    min-height: 62px;

    margin-bottom: 10px;

    overflow: hidden;

    border:
        1px solid #252525;

    background:
        #090909;

    display: flex;

    align-items: center;
}

.flag-large {

    position: absolute;

    left: -14px;

    top: 0;

    width: 190px;

    height: 62px;

    transform:
        skewX(-12deg);

    background-color:
        #ffffff;

    background-image:

        linear-gradient(
            45deg,
            #050505 25%,
            transparent 25%,
            transparent 75%,
            #050505 75%
        ),

        linear-gradient(
            45deg,
            #050505 25%,
            transparent 25%,
            transparent 75%,
            #050505 75%
        );

    background-position:
        0 0,
        20px 20px;

    background-size:
        40px 40px;

    opacity: 0.9;
}

.flag-large::after {

    content: "";

    position: absolute;

    inset: 0;

    background:
        linear-gradient(
            90deg,
            transparent,
            rgba(9,9,9,0.05) 30%,
            #090909 100%
        );
}

.flag-zone-label {

    position: relative;

    z-index: 2;

    margin-left: 155px;

    color:
        #858585;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size: 14px;

    font-weight: 700;

    letter-spacing: 2px;

    text-transform: uppercase;
}

.flag-zone-label span {
    color: #e10600;
}

/* ============================================================
   CONTROLS
   ============================================================ */

.control-bar {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 12px;

    margin-bottom: 18px;

    position: relative;

    z-index: 10000;
}

.control {

    position: relative;

    padding:
        11px 13px 12px;

    background:
        #0c0c0c;

    border:
        1px solid #292929;

    z-index: 10000;
}

.control:first-child {
    z-index: 11000;
}

.control:last-child {
    z-index: 10000;
}

.control-label {

    display: block;

    margin-bottom: 7px;

    color:
        #626262;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 1.7px;

    text-transform: uppercase;
}

.control-label-red {
    color: #e10600;
}


.control::before {

    content: "";

    position: absolute;

    left: 0;
    top: 0;
    bottom: 0;

    width: 3px;

    background:
        #e10600;

    z-index: 1;
}

/* ============================================================
   CUSTOM DROPDOWN
   ============================================================ */

.racing-dropdown {

    position: relative;

    width: 100%;

    z-index: 100000;
}

.racing-dropdown-button {

    width: 100%;

    height: 42px;

    padding:
        0 13px 0 16px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    background:
        #111111 !important;

    color:
        #ffffff !important;

    border:
        1px solid #3d3d3d;

    border-radius: 2px;

    font-family:
        "Inter",
        Arial,
        sans-serif;

    font-size: 11px;

    font-weight: 600;

    text-align: left;

    cursor: pointer;

    outline: none;

    appearance: none;

    -webkit-appearance: none;

    transition:
        border-color 0.15s ease,
        background 0.15s ease;
}

.racing-dropdown-button:hover,
.racing-dropdown-button:focus {

    background:
        #151515 !important;

    border-color:
        #e10600 !important;

    color:
        #ffffff !important;

    outline: none !important;

    box-shadow:
        0 0 0 1px
        rgba(225,6,0,0.15);
}

/* ============================================================
   CHEVRON
   ============================================================ */

.racing-dropdown-chevron {

    width: 9px;
    height: 9px;

    flex-shrink: 0;

    margin-left: 12px;

    border-right:
        2px solid #8a8a8a;

    border-bottom:
        2px solid #8a8a8a;

    transform:
        rotate(45deg)
        translateY(-2px);

    transition:
        transform 0.18s ease,
        border-color 0.18s ease;
}

.racing-dropdown-button:hover
.racing-dropdown-chevron {

    border-color:
        #e10600;
}

.racing-dropdown.open
.racing-dropdown-chevron {

    transform:
        rotate(225deg)
        translateY(-1px);
}

/* ============================================================
   DROPDOWN MENU
   ============================================================ */

.racing-dropdown-menu {

    display: none;

    position: absolute;

    left: 0;
    right: 0;

    top:
        calc(100% + 3px);

    width: 100%;

    max-height: 260px;

    overflow-y: auto;

    padding: 4px;

    background:
        #111111 !important;

    border:
        1px solid #3d3d3d;

    box-shadow:
        0 18px 40px
        rgba(0,0,0,0.95);

    z-index:
        2147483647;
}

.racing-dropdown.open
.racing-dropdown-menu {

    display: block;
}

/* ============================================================
   DROPDOWN OPTIONS
   ============================================================ */

.racing-dropdown-option {

    display: block;

    width: 100%;

    min-height: 40px;

    padding:
        10px 12px;

    border: none;

    border-radius: 1px;

    background:
        #111111 !important;

    color:
        #d6d6d6 !important;

    font-family:
        "Inter",
        Arial,
        sans-serif;

    font-size: 11px;

    font-weight: 600;

    text-align: left;

    cursor: pointer;

    appearance: none;

    -webkit-appearance: none;

    transition:
        background 0.12s ease,
        color 0.12s ease;
}

.racing-dropdown-option:hover {

    background:
        #650b08 !important;

    color:
        #ffffff !important;
}

.racing-dropdown-option.selected {

    background:
        #e10600 !important;

    color:
        #ffffff !important;

    font-weight: 800;

    box-shadow:
        inset 3px 0 0
        #ff5a54;
}

.racing-dropdown-option.selected:hover {

    background:
        #ff251d !important;

    color:
        #ffffff !important;
}

/* ============================================================
   SCROLLBAR
   ============================================================ */

.racing-dropdown-menu::-webkit-scrollbar {
    width: 5px;
}

.racing-dropdown-menu::-webkit-scrollbar-track {
    background: #090909;
}

.racing-dropdown-menu::-webkit-scrollbar-thumb {
    background: #444444;
}

.racing-dropdown-menu::-webkit-scrollbar-thumb:hover {
    background: #e10600;
}

/* ============================================================
   TELEMETRY
   ============================================================ */

.telemetry {

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 1px;

    margin-bottom: 18px;

    background:
        #292929;

    border:
        1px solid #292929;
}

.telemetry-card {

    position: relative;

    overflow: hidden;

    padding:
        15px 18px;

    background:
        #0b0b0b;
}

.telemetry-card::after {

    content: "";

    position: absolute;

    right: -25px;
    top: -25px;

    width: 75px;
    height: 75px;

    border-radius: 50%;

    border:
        1px solid
        rgba(225,6,0,0.2);
}

.telemetry-label {

    color:
        #5f5f5f;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 1.6px;

    text-transform: uppercase;
}

.telemetry-value {

    margin-top: 5px;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size: 33px;

    line-height: 1;

    font-weight: 700;
}

.telemetry-unit {

    margin-left: 5px;

    color:
        #e10600;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 1px;
}

/* ============================================================
   MAP
   ============================================================ */

.map-frame {

    position: relative;

    overflow: visible;

    background:
        #080b0f;

    border:
        1px solid #272727;
}

.map-frame::before {

    content: "";

    position: absolute;

    left: 0;
    top: 0;
    right: 0;

    height: 2px;

    z-index: 100;

    background:
        #e10600;

    pointer-events: none;
}

.map-topbar {

    height: 45px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding:
        0 16px;

    background:
        #0c0c0c;

    border-bottom:
        1px solid #202020;
}

.map-title {

    display: flex;

    align-items: center;

    gap: 9px;

    font-family:
        "Barlow Condensed",
        sans-serif;

    font-size: 15px;

    font-weight: 700;

    letter-spacing: 1px;

    text-transform: uppercase;
}

.map-title::before {

    content: "";

    width: 7px;
    height: 7px;

    background:
        #e10600;

    box-shadow:
        0 0 10px
        rgba(225,6,0,0.8);
}

.map-meta {

    display: flex;

    align-items: center;

    gap: 7px;

    color:
        #515151;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 1.5px;

    text-transform: uppercase;
}

.map-frame .js-plotly-plot,
.map-frame .plot-container,
.map-frame .plotly {

    background:
        #080b0f !important;
}

.map-frame .main-svg {

    background:
        transparent !important;
}

.desktop-map {
    display: block;
}

.mobile-map {
    display: none;
}

/* ============================================================
   FOOTER
   ============================================================ */

.footer {

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding:
        14px 2px 0;

    color:
        #3d3d3d;

    font-size: 8px;

    font-weight: 800;

    letter-spacing: 1.2px;

    text-transform: uppercase;
}

.footer-red {
    color: #e10600;
}

/* ============================================================
   TABLET
   ============================================================ */

@media (max-width: 900px) {

    .race-app {
        padding:
            0 15px 30px;
    }

    .telemetry {
        grid-template-columns:
            1fr 1fr;
    }

    .map-meta {
        display: none;
    }
}

/* ============================================================
   PORTRAIT
   ============================================================ */

@media (max-width: 700px) {

    .race-app {
        padding:
            0 10px 25px;
    }

    .topbar {
        padding-top: 16px;
    }

    .header-content {
        position: relative;
        z-index: 2;
    }

    .checker-flag {
        width: 46px;
        height: 46px;
        flex: 0 0 46px;

        background-size: 16px 16px;
        background-position: 0 0, 8px 8px;
    }

    .series-title {
        font-size: 24px;
    }

    .series-subtitle {

        font-size: 7px;

        letter-spacing: 1.4px;
    }

    .hub-link {

        height: 38px;

        padding:
            0 12px;

        font-size: 7px;

        letter-spacing: 0.9px;
    }

    .hero {
        padding-top: 27px;
    }

    .hero-title {
        font-size: 48px;
    }

    .flag {
        right: -45px;
        top: 50%;
        width: 300px;
        height: 150px;
        opacity: 0.075;
        transform:
            translateY(-50%)
            skew(-15deg)
            perspective(500px)
            rotateY(-20deg);
        z-index: 0;
    }

    /* Checker control strip */

    .flag-control-zone {
        min-height: 57px;
    }

    .flag-large {

        width: 145px;

        height: 57px;

        background-size:
            32px 32px;

        background-position:
            0 0,
            16px 16px;
    }

    .flag-zone-label {

        margin-left: 118px;

        font-size: 10px;

        letter-spacing: 1.3px;
    }


    /* Stacked controls */

    .control-bar {

        grid-template-columns:
            1fr;

        gap: 10px;
    }

    .control:first-child {
        z-index: 20000;
    }

    .control:last-child {
        z-index: 10000;
    }

    .telemetry-value {
        font-size: 28px;
    }


    /* Mobile map */

    .desktop-map {
        display: none;
    }

    .mobile-map {
        display: block;
    }

    .map-topbar {
        height: 42px;
    }

    .map-title {
        font-size: 13px;
    }
}

/* ============================================================
   SMALL PHONES
   ============================================================ */

@media (max-width: 400px) {

    .brand {
        gap: 7px;
    }

    .checker-flag {
        width: 42px;
        height: 42px;
        flex-basis: 42px;
    }

    .series-title {
        font-size: 21px;
    }

    .series-subtitle {
        display: none;
    }

    .hero-title {
        font-size: 42px;
    }

    .telemetry {
        grid-template-columns:
            1fr;
    }

    .flag-zone-label {

        margin-left: 103px;

        font-size: 8px;
    }
}

</style>

</head>

<body>

    {%app_entry%}

    <footer>

        {%config%}
        {%scripts%}
        {%renderer%}

    </footer>


<script>

/* ============================================================
   CUSTOM DROPDOWN UI
   ============================================================ */

(function () {

    function closeAllDropdowns(except) {

        document
            .querySelectorAll(
                ".racing-dropdown.open"
            )
            .forEach(function (dropdown) {

                if (dropdown !== except) {

                    dropdown.classList.remove(
                        "open"
                    );
                }
            });
    }

    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    ".racing-dropdown-button"
                );

            const option =
                event.target.closest(
                    ".racing-dropdown-option"
                );

            const dropdown =
                event.target.closest(
                    ".racing-dropdown"
                );

            /* --------------------------------------------
               BUTTON
               -------------------------------------------- */

            if (button) {

                const parent =
                    button.closest(
                        ".racing-dropdown"
                    );

                if (!parent) {
                    return;
                }

                const wasOpen =
                    parent.classList.contains(
                        "open"
                    );

                closeAllDropdowns(parent);

                if (wasOpen) {

                    parent.classList.remove(
                        "open"
                    );

                } else {

                    parent.classList.add(
                        "open"
                    );
                }
                return;
            }

            /* --------------------------------------------
               OPTION
               -------------------------------------------- */

            if (option) {

                const parent =
                    option.closest(
                        ".racing-dropdown"
                    );

                if (parent) {

                    setTimeout(
                        function () {

                            parent.classList.remove(
                                "open"
                            );

                        },
                        40
                    );
                }
                return;
            }

            /* --------------------------------------------
               OUTSIDE CLICK
               -------------------------------------------- */

            if (!dropdown) {
                closeAllDropdowns(null);
            }
        },
        true
    );

})();

</script>

</body>

</html>

"""

# ============================================================
# LAYOUT
# ============================================================

app.layout = html.Div(

    className="race-app",

    children=[

        html.Div(
            className="race-stripe"
        ),

        html.Div(

            className="race-container",

            children=[

                # ====================================================
                # HEADER
                # ====================================================

                html.Div(

                    className="topbar",

                    children=[

                        html.Div(

                            className="brand",

                            children=[

                                html.Div(
                                    className="checker-flag"
                                ),

                                html.Div(

                                    [

                                        html.H1(
                                            "AutoDRIVE-RoboRacer",
                                            className=
                                                "series-title"
                                        ),

                                        html.Div(
                                            [
                                                "SIM RACING LEAGUES ",
        
                                                html.Span(
                                                    "// GLOBAL GRID"
                                                ),
                                            ],
                                            
                                            className=
                                                "series-subtitle"
                                        ),
                                    ]
                                ),

                            ],
                        ),


                        html.Div(

                            className="header-right",

                            children=[

                                html.A(
                                    [
                                        "COMPETITION HUB",

                                        html.Span(
                                            "open_in_new",
                                            className="material-symbols-outlined",
                                        ),
                                    ],

                                    href=(
                                        "https://autodrive-ecosystem."
                                        "github.io/competitions"
                                    ),

                                    target="_blank",

                                    className="hub-link",
                                ),
                            ],
                        ),
                    ],
                ),

                # ====================================================
                # HERO
                # ====================================================

                html.Div(

                    className="hero",

                    children=[

                        html.Div(
                            className="flag"
                        ),

                        html.Div(

                            className=
                                "hero-content",

                            children=[

                                html.Div(
                                    [
                                        "GLOBAL PARTICIPATION ",

                                        html.Span(
                                            "// ANALYTICS",
                                        ),
                                    ],

                                    className=
                                        "hero-kicker"
                                ),

                                html.H2(

                                    [

                                        html.Span(
                                            "///",
                                            className="red"
                                        ),

                                        "THE GLOBAL GRID FOR",

                                        html.Br(),

                                        html.Span(
                                            "AUTONOMOUS SIM RACING",
                                            className="red"
                                        ),

                                    ],

                                    className=
                                        "hero-title",
                                ),

                                html.Div(
                                    "Tracking the worldwide impact of AutoDRIVE-RoboRacer Sim Racing Leagues.",
                                    className=
                                        "hero-description",
                                ),

                            ],
                        ),

                    ],
                ),

                # ====================================================
                # CHECKERBOARD STRIP
                # ====================================================

                html.Div(

                    className=
                        "flag-control-zone",

                    children=[

                        html.Div(
                            className="flag-large"
                        ),

                        html.Div(

                            [

                                "STARTING GRID ",

                                html.Span(
                                    "// SELECT SESSION"
                                ),

                            ],

                            className=
                                "flag-zone-label",
                        ),

                    ],
                ),

                # ====================================================
                # CONTROLS
                # ====================================================

                html.Div(

                    className=
                        "control-bar",

                    children=[

                        html.Div(

                            className="control",

                            children=[

                                html.Label(
                                    [
                                        "SELECT ",
                                        html.Span(
                                            "// RACE EVENT",
                                            className="control-label-red",
                                        ),
                                    ],
                                    className="control-label",
                                ),

                                racing_dropdown(

                                    "competition-select",

                                    competition_options,

                                    "All Competitions",

                                ),

                            ],
                        ),

                        html.Div(

                            className="control",

                            children=[

                                html.Label(
                                    [
                                        "SELECT ",
                                        html.Span(
                                            "// ANALYTICS METRIC",
                                            className="control-label-red",
                                        ),
                                    ],
                                    className="control-label",
                                ),

                                racing_dropdown(

                                    "metric-select",

                                    get_metric_options(
                                        "All Competitions"
                                    ),

                                    "Teams",

                                ),

                            ],
                        ),

                    ],
                ),

                # ====================================================
                # TELEMETRY
                # ====================================================

                html.Div(

                    className="telemetry",

                    children=[

                        html.Div(

                            className=
                                "telemetry-card",

                            children=[

                                html.Div(
                                    "TOTAL PARTICIPANTS",
                                    className=
                                        "telemetry-label",
                                ),

                                html.Div(

                                    [

                                        html.Span(
                                            "0",
                                            id=
                                                "kpi-participants",
                                            className=
                                                "telemetry-value",
                                        ),

                                        html.Span(
                                            "RACERS",
                                            className=
                                                "telemetry-unit",
                                        ),

                                    ]
                                ),

                            ],
                        ),

                        html.Div(

                            className=
                                "telemetry-card",

                            children=[

                                html.Div(
                                    "REGISTERED TEAMS",
                                    className=
                                        "telemetry-label",
                                ),

                                html.Div(

                                    [

                                        html.Span(
                                            "0",
                                            id=
                                                "kpi-teams",
                                            className=
                                                "telemetry-value",
                                        ),

                                        html.Span(
                                            "ENTITIES",
                                            className=
                                                "telemetry-unit",
                                        ),
                                    ]
                                ),
                            ],
                        ),

                        html.Div(

                            className=
                                "telemetry-card",

                            children=[

                                html.Div(
                                    "ORGANIZATIONS",
                                    className=
                                        "telemetry-label",
                                ),

                                html.Div(
                                    [
                                        html.Span(
                                            "0",
                                            id=
                                                "kpi-organizations",
                                            className=
                                                "telemetry-value",
                                        ),

                                        html.Span(
                                            "INSTITUTIONS",
                                            className=
                                                "telemetry-unit",
                                        ),
                                    ]
                                ),
                            ],
                        ),

                        html.Div(

                            className=
                                "telemetry-card",

                            children=[

                                html.Div(
                                    "COUNTRIES",
                                    className=
                                        "telemetry-label",
                                ),

                                html.Div(
                                    [
                                        html.Span(
                                            "0",
                                            id=
                                                "kpi-countries",
                                            className=
                                                "telemetry-value",
                                        ),

                                        html.Span(
                                            "NATIONS",
                                            className=
                                                "telemetry-unit",
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),

                # ====================================================
                # MAP
                # ====================================================

                html.Div(

                    className="map-frame",

                    children=[

                        html.Div(

                            className="map-topbar",

                            children=[

                                html.Div(
                                    "WORLDWIDE PARTICIPATION",
                                    className=
                                        "map-title",
                                ),

                                html.Div(
                                    className="map-meta",

                                    children=[

                                        html.Span(
                                            className="live-dot"
                                        ),
                                        "LIVE REGISTRATION TELEMETRY",
                                    ],
                                ),
                            ],
                        ),

                        dcc.Graph(

                            id="desktop-map",

                            className=
                                "desktop-map",

                            style={
                                "height": "680px"
                            },

                            config={

                                "displayModeBar":
                                    False,

                                "responsive":
                                    True,

                                "scrollZoom":
                                    False,

                                "doubleClick":
                                    False,

                            },
                        ),

                        dcc.Graph(

                            id="mobile-map",

                            className=
                                "mobile-map",

                            style={
                                "height": "620px"
                            },

                            config={

                                "displayModeBar":
                                    False,

                                "responsive":
                                    True,

                                "scrollZoom":
                                    False,

                                "doubleClick":
                                    False,
                            },
                        ),
                    ],
                ),

                # ====================================================
                # FOOTER
                # ====================================================

                html.Div(

                    className="footer",

                    children=[

                        html.Div(

                            [

                                "AUTODRIVE-ROBORACER SIM RACING LEAGUES ",

                                html.Span(
                                    "// GLOBAL GRID",
                                    className=
                                        "footer-red",
                                ),

                            ]
                        ),

                        html.Div(
                            "PARTICIPATION ANALYTICS"
                        ),
                    ],
                ),
            ],
        ),
    ],
)

# ============================================================
# DROPDOWN OPTION SELECTION
# ============================================================

@app.callback(

    Output(
        {
            "type":
                "racing-dropdown-value",
            "id":
                ALL,
        },
        "children",
    ),

    Output(
        {
            "type":
                "racing-dropdown-store",
            "id":
                ALL,
        },
        "data",
    ),

    Output(
        {
            "type":
                "racing-dropdown-option",
            "dropdown":
                ALL,
            "value":
                ALL,
        },
        "className",
    ),

    Input(
        {
            "type":
                "racing-dropdown-option",
            "dropdown":
                ALL,
            "value":
                ALL,
        },
        "n_clicks",
    ),

    State(
        {
            "type":
                "racing-dropdown-store",
            "id":
                ALL,
        },
        "data",
    ),

    State(
        {
            "type":
                "racing-dropdown-value",
            "id":
                ALL,
        },
        "children",
    ),

    State(
        {
            "type":
                "racing-dropdown-option",
            "dropdown":
                ALL,
            "value":
                ALL,
        },
        "id",
    ),

    prevent_initial_call=True,
)
def select_dropdown_option(
    clicks,
    current_values,
    current_labels,
    option_ids,
):

    values = list(current_values)

    triggered = ctx.triggered_id

    if triggered is None:

        return (
            current_labels,
            values,
            [
                "racing-dropdown-option"
                for _ in option_ids
            ],
        )

    dropdown = triggered["dropdown"]
    selected_value = triggered["value"]

    # --------------------------------------------------------
    # UPDATE ONLY THE CLICKED DROPDOWN
    # --------------------------------------------------------

    if dropdown == "competition-select":

        values[0] = selected_value

        # If switching away from All Competitions,
        # Participation is no longer valid.
        if (
            selected_value
            != "All Competitions"
            and values[1]
            == "Participation"
        ):
            values[1] = "Teams"

    elif dropdown == "metric-select":

        values[1] = selected_value

    # --------------------------------------------------------
    # DISPLAY LABELS
    # --------------------------------------------------------

    display_values = [

        competition_labels.get(
            values[0],
            values[0],
        ),

        metric_labels.get(
            values[1],
            values[1],
        ),
    ]

    # --------------------------------------------------------
    # SELECTED OPTION CLASSES
    # --------------------------------------------------------

    classes = []

    for option_id in option_ids:

        option_dropdown = (
            option_id["dropdown"]
        )

        option_value = (
            option_id["value"]
        )

        selected = (
            option_dropdown
            == "competition-select"
            and
            option_value
            == values[0]
        ) or (
            option_dropdown
            == "metric-select"
            and
            option_value
            == values[1]
        )

        if selected:
            classes.append(
                "racing-dropdown-option selected"
            )
        else:
            classes.append(
                "racing-dropdown-option"
            )

    return (
        display_values,
        values,
        classes,
    )

# ============================================================
# UPDATE METRIC DROPDOWN WHEN COMPETITION CHANGES
# ============================================================

@app.callback(

    Output(
        {
            "type":
                "racing-dropdown-menu",
            "id":
                "metric-select",
        },
        "children",
    ),

    Input(
        {
            "type":
                "racing-dropdown-store",
            "id":
                "competition-select",
        },
        "data",
    ),

    State(
        {
            "type":
                "racing-dropdown-store",
            "id":
                "metric-select",
        },
        "data",
    ),
)
def update_metric_options(
    selected_competition,
    selected_metric,
):

    if not selected_competition:
        selected_competition = (
            "All Competitions"
        )

    valid_metrics = [
        "Teams",
        "Participants",
        "Organizations",
    ]

    if (
        selected_competition
        == "All Competitions"
    ):
        valid_metrics.append(
            "Participation"
        )

    if selected_metric not in valid_metrics:
        selected_metric = "Teams"


    return [

        html.Button(

            metric_labels[
                metric
            ],

            id={
                "type":
                    "racing-dropdown-option",

                "dropdown":
                    "metric-select",

                "value":
                    metric,
            },

            className=(
                "racing-dropdown-option"
                +
                (
                    " selected"
                    if metric
                    == selected_metric
                    else ""
                )
            ),

            n_clicks=0,

        )

        for metric in valid_metrics

    ]

# ============================================================
# MAP BUILDER
# ============================================================

def build_map_figure(
    df_subset,
    selected_metric,
    selected_comp,
    portrait=False,
):

    df_subset = df_subset.copy()

    # ========================================================
    # HOVER TEXT
    # ========================================================

    hover_text = []

    for _, row in df_subset.iterrows():

        country = str(
            row["COUNTRY"]
        ).upper()

        text = (

            f"<b>{country}</b>"

            "<br><br>"

            f"<b>Teams:</b> "
            f"{int(row['Teams'])}"

            "<br>"

            f"<b>Participants:</b> "
            f"{int(row['Participants'])}"

            "<br>"

            f"<b>Organizations:</b> "
            f"{int(row['Organizations'])}"

        )

        if (
            selected_comp
            == "All Competitions"
        ):

            text += (

                "<br>"

                f"<b>Competitions:</b> "
                f"{int(row['Participation'])}"

            )

        hover_text.append(text)

    df_subset["hover_text"] = (
        hover_text
    )

    # ========================================================
    # COLOR SCALE
    # ========================================================

    color_scale = [
        [0.00, "#063B70"],
        [0.12, "#075F91"],
        [0.25, "#00A9D6"],
        [0.40, "#00D9C0"],
        [0.55, "#35E66A"],
        [0.68, "#D7F000"],
        [0.80, "#FFD000"],
        [0.90, "#FF7500"],
        [1.00, "#FF1E1E"],
    ]

    # ========================================================
    # CHOROPLETH
    # ========================================================

    fig = px.choropleth(
        df_subset,

        locations="COUNTRY",

        locationmode=
            "country names",

        color=
            selected_metric,

        color_continuous_scale=
            color_scale,
    )

    # ========================================================
    # TRACE
    # ========================================================

    fig.update_traces(

        customdata=
            df_subset[
                ["hover_text"]
            ].values,

        hovertemplate=
            "%{customdata[0]}"
            "<extra></extra>",

        marker_line_color=
            "#E10600",

        marker_line_width=
            0.7,

    )

    # ========================================================
    # GEO
    # ========================================================

    fig.update_geos(

        bgcolor=
            "#080B0F",

        showland=
            True,

        landcolor=
            "#151B22",

        showocean=
            True,

        oceancolor=
            "#06090D",

        showlakes=
            True,

        lakecolor=
            "#070B10",

        showcountries=
            True,

        countrycolor=
            "#4B5663",

        countrywidth=
            0.7,

        showcoastlines=
            True,

        coastlinecolor=
            "#667381",

        coastlinewidth=
            0.8,

        projection_type=
            "natural earth",

        resolution=
            50,

    )

    # ========================================================
    # COLORBAR
    # ========================================================

    max_val = df_subset[
        selected_metric
    ].max()

    dtick = (

        1

        if max_val <= 20

        else max(
            1,
            round(max_val / 6),
        )
    )

    if portrait:

        colorbar = dict(

            orientation="h",

            title=dict(

                text=
                    metric_labels[
                        selected_metric
                    ].upper(),

                side="top",

                font=dict(
                    size=9,
                    color="#FFFFFF",
                ),
            ),

            tickfont=dict(
                size=9,
                color="#FFFFFF",
            ),

            thickness=13,

            len=0.72,

            x=0.5,

            xanchor="center",

            y=-0.035,

            yanchor="top",

            bgcolor="#080B0F",

            bordercolor="#46515E",

            borderwidth=1,

            outlinecolor="#687582",

            outlinewidth=1,

            tickmode="linear",

            tick0=0,

            dtick=dtick,

        )

        margin = dict(
            l=0,
            r=0,
            t=5,
            b=90,
        )

    else:

        colorbar = dict(

            orientation="v",

            title=dict(

                text=
                    metric_labels[
                        selected_metric
                    ].upper(),

                side="right",

                font=dict(
                    size=10,
                    color="#FFFFFF",
                ),
            ),

            tickfont=dict(
                size=10,
                color="#FFFFFF",
            ),

            thickness=15,

            len=0.60,

            x=0.97,

            xanchor="left",

            y=0.50,

            yanchor="middle",

            bgcolor="#080B0F",

            bordercolor="#46515E",

            borderwidth=1,

            outlinecolor="#687582",

            outlinewidth=1,

            tickmode="linear",

            tick0=0,

            dtick=dtick,

        )

        margin = dict(
            l=0,
            r=0,
            t=5,
            b=0,
        )

    fig.update_coloraxes(
        colorbar=colorbar
    )

    # ========================================================
    # FINAL LAYOUT
    # ========================================================

    fig.update_layout(

        paper_bgcolor=
            "#080B0F",

        plot_bgcolor=
            "#080B0F",

        font=dict(

            family=
                "Inter, Arial, sans-serif",

            color=
                "#FFFFFF",
        ),

        margin=
            margin,

        hoverlabel=dict(

            bgcolor=
                "#0B1118",

            bordercolor=
                "#E10600",

            font=dict(

                family=
                    "Inter",

                size=
                    11,

                color=
                    "#FFFFFF",
            ),

            align=
                "left",
        ),
    )

    return fig

# ============================================================
# MAIN DATA CALLBACK
# ============================================================

@app.callback(

    Output(
        "desktop-map",
        "figure",
    ),

    Output(
        "mobile-map",
        "figure",
    ),

    Output(
        "kpi-participants",
        "children",
    ),

    Output(
        "kpi-teams",
        "children",
    ),

    Output(
        "kpi-organizations",
        "children",
    ),

    Output(
        "kpi-countries",
        "children",
    ),

    Input(
        {
            "type":
                "racing-dropdown-store",

            "id":
                "competition-select",
        },

        "data",
    ),

    Input(
        {
            "type":
                "racing-dropdown-store",

            "id":
                "metric-select",
        },

        "data",
    ),

)
def update_map(

    selected_comp,
    selected_metric,

):

    if not selected_comp:

        selected_comp = (
            "All Competitions"
        )

    if not selected_metric:

        selected_metric = "Teams"

    # ========================================================
    # VALID METRICS
    # ========================================================

    valid_metrics = [
        "Teams",
        "Participants",
        "Organizations",
    ]

    if (
        selected_comp
        == "All Competitions"
    ):

        valid_metrics.append(
            "Participation"
        )


    if (
        selected_metric
        not in valid_metrics
    ):

        selected_metric = "Teams"

    # ========================================================
    # FILTER
    # ========================================================

    df_subset = map_data[
        map_data["Competition"]
        ==
        selected_comp
    ].copy()

    # ========================================================
    # NUMBERS
    # ========================================================

    numeric_cols = [

        "Teams",
        "Participants",
        "Organizations",
        "Participation",

    ]

    for col in numeric_cols:

        if col in df_subset.columns:

            df_subset[col] = (

                df_subset[col]

                .fillna(0)

                .astype(int)

            )

    # ========================================================
    # TOTALS
    # ========================================================

    total_participants = int(
        df_subset[
            "Participants"
        ].sum()
    )

    total_teams = int(
        df_subset[
            "Teams"
        ].sum()
    )

    total_organizations = int(
        df_subset[
            "Organizations"
        ].sum()
    )

    total_countries = int(
        df_subset[
            "COUNTRY"
        ].nunique()
    )

    # ========================================================
    # FIGURES
    # ========================================================

    desktop_fig = build_map_figure(

        df_subset,

        selected_metric,

        selected_comp,

        portrait=False,

    )

    mobile_fig = build_map_figure(

        df_subset,

        selected_metric,

        selected_comp,

        portrait=True,

    )

    return (

        desktop_fig,

        mobile_fig,

        f"{total_participants:,}",

        f"{total_teams:,}",

        f"{total_organizations:,}",

        f"{total_countries:,}",

    )

# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=False,

        host="0.0.0.0",

        port=port,

        threaded=True,

    )