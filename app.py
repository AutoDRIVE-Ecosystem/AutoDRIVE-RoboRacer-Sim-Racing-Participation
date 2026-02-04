import pandas as pd
from dash import Dash, dcc, html, Output, Input
import plotly.express as px

# -------------------------
# Competition order
# -------------------------
competition_order = ["IROS 2024", "CDC 2024", "ICRA 2025", "CDC-TF 2025"]

# -------------------------
# Load and clean data
# -------------------------
def load_competition(sheet_name):
    df = pd.read_excel("Registration.xlsx", sheet_name=sheet_name, header=None)
    df.columns = ['SR NO', 'TEAM NAME', 'TEAM MEMBER', 'ORGANIZATION', 'COUNTRY']
    df[['SR NO', 'TEAM NAME', 'ORGANIZATION', 'COUNTRY']] = df[['SR NO', 'TEAM NAME', 'ORGANIZATION', 'COUNTRY']].ffill()
    df = df.dropna(subset=['TEAM MEMBER'])
    df["Competition"] = sheet_name
    return df

all_data = pd.concat([load_competition(c) for c in competition_order], ignore_index=True)

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
df_split['COUNTRY'] = df_split['COUNTRY'].str.replace(r'\s*&\s*|\s*/\s*|\s+and\s+', ',', regex=True)
df_split['COUNTRY'] = df_split['COUNTRY'].str.split(',')
df_split = df_split.explode('COUNTRY')
df_split['COUNTRY'] = df_split['COUNTRY'].str.strip()
df_split['COUNTRY'] = df_split['COUNTRY'].replace(country_alias_map)

# -------------------------
# Aggregate stats
# -------------------------
per_competition = (
    df_split.groupby(['Competition', 'COUNTRY'])
    .agg(Teams=('TEAM NAME', 'nunique'),
         Participants=('TEAM MEMBER', 'count'),
         Organizations=('ORGANIZATION', 'nunique'))
    .reset_index()
)

all_combined = (
    df_split.groupby('COUNTRY')
    .agg(Teams=('TEAM NAME', 'nunique'),
         Participants=('TEAM MEMBER', 'count'),
         Organizations=('ORGANIZATION', 'nunique'),
         Participation=('Competition', 'nunique'))
    .reset_index()
)
all_combined['Competition'] = 'All Competitions'

map_data = pd.concat([per_competition, all_combined], ignore_index=True)

# -------------------------
# Metric labels
# -------------------------
metric_labels = {
    'Teams': 'Number of Teams',
    'Participants': 'Number of Participants',
    'Organizations': 'Number of Organizations',
    'Participation': 'Number of Competitions'
}

# -------------------------
# Dash App
# -------------------------
app = Dash(__name__)
app.title = "Global Participation Map"

app.layout = html.Div([
    html.H2("🏎️ RoboRacer Sim Racing League", style={'textAlign': 'center'}),
    html.H3(
        html.A("https://autodrive-ecosystem.github.io/competitions",
               href="https://autodrive-ecosystem.github.io/competitions",
               target="_blank"),
        style={'textAlign': 'center'}
    ),
    html.Div("Select Competition and Metric:", style={'margin-top': '20px', 'margin-bottom': '5px'}),
    html.Div([
        dcc.Dropdown(
            id='competition-dropdown',
            options=[{'label': c, 'value': c} for c in ['All Competitions'] + competition_order],
            value='All Competitions',
            clearable=False,
            style={'width': '250px', 'display': 'inline-block', 'margin-right': '20px'}
        ),
        dcc.Dropdown(
            id='metric-dropdown',
            value='Teams',
            clearable=False,
            style={'width': '250px', 'display': 'inline-block'}
        )
    ], style={'margin-bottom': '20px'}),
    dcc.Graph(id='choropleth-map', style={'height': '650px'})
], style={'padding': '20px',
          'font-family': 'Roboto, Arial, sans-serif',
          'color': '#2c3e50'})

# -------------------------
# Callback
# -------------------------
@app.callback(
    Output('metric-dropdown', 'options'),
    Output('metric-dropdown', 'value'),
    Output('choropleth-map', 'figure'),
    Input('competition-dropdown', 'value'),
    Input('metric-dropdown', 'value')
)
def update_map(selected_comp, selected_metric):
    df_subset = map_data[map_data['Competition'] == selected_comp].copy()

    # Fill NaNs and ensure integers
    numeric_cols = ['Teams', 'Participants', 'Organizations', 'Participation']
    for col in numeric_cols:
        if col in df_subset.columns:
            df_subset[col] = df_subset[col].fillna(0).astype(int)

    # Determine valid metrics
    all_metrics = list(metric_labels.keys())
    if selected_comp != "All Competitions":
        valid_metrics = [m for m in all_metrics if m != "Participation"]
    else:
        valid_metrics = all_metrics

    # Reset metric if invalid
    if selected_metric not in valid_metrics:
        selected_metric = valid_metrics[0]

    # Build dropdown options
    metric_options = [{'label': metric_labels[m], 'value': m} for m in valid_metrics]

    # Compute totals for title
    total_participants = df_subset['Participants'].sum()
    total_teams = df_subset['Teams'].sum()
    total_organizations = df_subset['Organizations'].sum()
    total_countries = df_subset['COUNTRY'].nunique()

    # Determine hover columns
    hover_cols = ['Teams', 'Participants', 'Organizations']
    if selected_comp == "All Competitions":
        hover_cols.append('Participation')

    # Create hover text with integers
    df_subset['hover_text'] = df_subset.apply(
        lambda row: (
            f"{row['COUNTRY']}<br>"
            f"Teams: {row['Teams']}<br>"
            f"Participants: {row['Participants']}<br>"
            f"Organizations: {row['Organizations']}"
            + (f"<br>Competitions: {row['Participation']}" if 'Participation' in hover_cols else "")
        ),
        axis=1
    )

    # Determine dtick for integer colorbar
    max_val = df_subset[selected_metric].max()
    dtick = 1 if max_val <= 20 else max(1, round(max_val / 6))

    # Create choropleth
    fig = px.choropleth(
        df_subset,
        locations='COUNTRY',
        locationmode='country names',
        color=selected_metric,
        color_continuous_scale='rainbow',
    )

    # Apply custom hover
    fig.update_traces(hovertemplate=df_subset['hover_text'])

    # Update layout
    fig.update_layout(
        title={
            "text": (
                f"🌍 Global Participation Map — {selected_comp} ({metric_labels[selected_metric]})<br>"
                f"<span style='font-size:12px; color:gray;'>"
                f"{total_participants} Participants | "
                f"{total_teams} Teams | "
                f"{total_organizations} Organizations | "
                f"{total_countries} Countries"
                f"</span>"
            ),
            "x": 0.5,
            "xanchor": "center"
        },
        geo=dict(showland=True, landcolor='lightgray', showocean=True, oceancolor='aliceblue'),
        margin=dict(l=100, r=50, t=140, b=50),
        coloraxis_colorbar=dict(
            title=dict(
                text=metric_labels[selected_metric],
                side="right",
                font=dict(size=12)
            ),
            tickangle=90,
            tickmode='linear',
            tick0=0,
            dtick=dtick,
            y=0.5,
            yanchor="middle",
            lenmode="fraction"
        )
    )

    return metric_options, selected_metric, fig

# -------------------------
# Run app
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)