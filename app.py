# app.py

import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import datetime

# Sort the data based on Date Index in ascending order
IE_Q = pd.read_csv("./assets/IE_Q.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
IE_Y = pd.read_csv("./assets/IE_Y.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
GDP_Q = pd.read_csv("./assets/GDP_Q.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
GDP_Y = pd.read_csv("./assets/GDP_Y.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
RS_Q = pd.read_csv("./assets/RS_Q.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
RS_Y = pd.read_csv("./assets/RS_Y.csv").set_index("Date").sort_index().loc["2011-01-01":"2019-12-31"]
TITLE_MAPPING = {"GDP": "Gross Domestic Products (GDP)", 
                 "RS": "Retail Sales", 
                 "IE": "Industrial Export", 
                 "Y": "Annual",
                 "Q": "Quarterly"}

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(
            children=f"Investment Analytics", 
            className="header-title",
        ),
        html.P(
            children=(
                "Analyze the behavior of various economic indicators between 2011 and 2019."
            ),
        ),
        html.Div([
            html.Label(html.B("Indicators:")),
            dcc.Dropdown(
                id="indicators",
                options=[
                    {"label": "GDP", "value": "GDP"},
                    {"label": "Retail Sales", "value": "RS"}, 
                    {"label": "Industrial Export", "value": "IE"}, 
                ],
                value="GDP"
            )
        ]),
        html.Div([
            html.Label(html.B("Transformation:")),
            dcc.Dropdown(
                id="transformation",
                options=[
                    {"label": "YoY", "value": "Y"},
                    {"label": "QoQ", "value": "Q"}, 
                ],
                value="Y"
            )
        ]),
        html.Div([
            html.Label(html.B("Country:")),
            dcc.Checklist(
                id="countries",
                options=[
                    {"label": "China", "value": "China"},
                    {"label": "United States (US)", "value": "US"},
                    {"label": "United Kingdom (UK)", "value": "UK"},
                ],
                value=["China", "US", "UK"],  # Set the default selected items (empty list for none selected)
            ),
        ]),
        html.Div([
            html.Label(html.B("Number of Quantiles:")),
            dcc.Dropdown(
                id="quantiles",
                options=[
                    {"label": "3", "value": "3"},
                    {"label": "5", "value": "5"}
                ],
                value="5",  # Set the default selected items (empty list for none selected)
            ),
        ]),
        html.Div([
            html.Label(html.B("End Period:  ")),
            dcc.Input(
                id="end",
                placeholder="Enter an end period (e.g. 2019-12-31)",
                type="text",
                value="2019-12-31"
            ),
            html.B(
                id="end_error",
                className="user-input-error",
                children=(
                    ""
                ),
            ),
        ]),
        html.Div([
            html.Label(html.B("Number of Lookback Periods:  ")),
            dcc.Input(
                id="lookback",
                type="text",
                placeholder="Enter the number of lookback period (e.g. 3)",
                value="10"
            ),
            html.B(
                id="lookback_error",
                className="user-input-error",
                children=(
                    ""
                ),
            ),
        ]),
        html.Div([
            dcc.Graph(
                id="heatmap",                   
            ),
        ]),
    ]
)

# Callback triggers changes to the graph based on user inputs.
# States are set to hold the user input values and trigger changes 
# ONLY AFTER inputs are blurred (the cursor moved away from the text input box).
@app.callback(
    [Output("heatmap", "figure"), Output("end_error", "children"), Output("lookback_error", "children")],
    [Input("indicators", "value"), Input("transformation", "value"), Input("countries", "value"), Input("quantiles", "value"), Input("lookback", "n_blur"), Input("end", "n_blur")],
    [State("heatmap", "figure"), State("lookback", "value"), State("end", "value")]
)
def filter_heatmap(indicators, transformation, countries, num_quantiles, lookback_blur, end_blur, prev_fig, lookback_val, end):
    # Select the correct csv file following the user input
    df = eval(str(indicators)+"_"+str(transformation))

    try:
        # Change heatmap title based on user inputs
        countries_in_text = ", ".join(countries[:-1]) + f" and {countries[-1]}" if len(countries) > 1 else countries[-1]
        heatmap_title = f"{TITLE_MAPPING[transformation]} Percentage Change in {TITLE_MAPPING[indicators]} for {countries_in_text}"
    except IndexError:
        # Except IndexError when no country was selected
        heatmap_title=f"{TITLE_MAPPING[transformation]} Percentage Change in {TITLE_MAPPING[indicators]}"

    try:
        # Throw error if the end period is not in ISO format
        datetime.date.fromisoformat(end)
        # Limit the output to show data before the user-specified end period
        df = df[countries].loc[:end]
    except:
        # Except ValueError when 
        return prev_fig, "Please use the date format: YYYY-MM-DD.", "" # error message for wrong end period input

    # Convert no. of quantiles to an integer
    num_quantiles = int(num_quantiles)

    try:
        # Sort the data based on Date Index in descending order to limit the lookback periods 
        df.sort_index(ascending=False, inplace=True)
        lookback = int(lookback_val)
        df = df.iloc[:lookback]
    except:
        return prev_fig, "", "Number of Lookback Periods should be an integer." # error message for wrong lookback input
    
    # Sort back the data
    df.sort_index(inplace=True)

    # Calculate quantiles and create the colorspace scale
    quantiles = np.linspace(0.0, 1.0, num=num_quantiles+1)
    color_continuous_scale= []
    if len(quantiles) == 4:
        color = ["purple", "white", "orange"]
        for i in range(len(quantiles)-1):
            color_continuous_scale.append((quantiles[i], color[i]))
            color_continuous_scale.append((quantiles[i+1], color[i]))
    elif len(quantiles) == 6:
        color = ["purple", "lightblue", "white", "yellow", "orange"]
        for i in range(len(quantiles)-1):
            color_continuous_scale.append((quantiles[i], color[i]))
            color_continuous_scale.append((quantiles[i+1], color[i]))
    
    # Use plotly Graph Objects to plot the heatmap
    heatmap = go.Heatmap(
                z=df.values.T,
                x=df.index,
                y=df.columns,
                colorscale=color_continuous_scale,
            )
    fig = go.Figure(
        data=heatmap,
    )
    # Show the values on top of heatmap
    fig.update_traces(text=df.values.T, texttemplate="<b>%{text:.2f}%</b>", hovertemplate=None)
    # Set the heatmap title and center it
    # Set the amount of padding between the plotting area and the axis lines
    fig.update_layout(title=heatmap_title, title_x=0.5, margin_pad=4)
    return fig, "", ""


if __name__ == "__main__":
    app.run_server(debug=True)