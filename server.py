import json

import dash
import pandas as pd
from dash import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output


def init_server(host="0.0.0.0", port=8080):
    app = dash.Dash(__name__)

    app.title = "ELEC3442 Chess Bot Analysis"
    app.layout = html.Div([html.H1("ELEC3442 Chess Bot Analysis", style={"textAlign": "center"}),
                           html.H6("Auto-updates every 3 seconds", style={"textAlign": "center"}),
                           dcc.Graph(id="cp-chart"), dash_table.DataTable(id="move-table",
                                                                          columns=[{"name": "Color", "id": "id"},
                                                                                   {"name": "Move Count",
                                                                                    "id": "move_count"},
                                                                                   {"name": "Your Move", "id": "move"},
                                                                                   {"name": "Best Move",
                                                                                    "id": "best_move"},
                                                                                   {"name": "Time Left (s)",
                                                                                    "id": "time_left"},
                                                                                   {"name": "Centipawn", "id": "cp"}, ],
                                                                          style_cell={"textAlign": "center"},
                                                                          style_header={
                                                                              "backgroundColor": "rgb(230, 230, 230)",
                                                                              "fontWeight": "bold", }, ),
                           dcc.Interval(id='interval-component', interval=3 * 1000,  # in milliseconds
                                        n_intervals=0), ],
                          style={"width": "80%", "margin": "auto", "font-family": "Comic Sans MS"})

    @app.callback(Output('cp-chart', 'figure'), Output('move-table', 'data'),
                  Input('interval-component', 'n_intervals'))
    def update_layout(n):
        try:
            with open("evaluation.json", "r") as f:
                data = json.load(f)
                print(data)

            df = pd.DataFrame(data)

            figure = {"data": [
                {"x": df[df["id"] == "black"]["move_count"], "y": df[df["id"] == "black"]["cp"], "type": "line",
                 "name": "Black", },
                {"x": df[df["id"] == "white"]["move_count"], "y": df[df["id"] == "white"]["cp"], "type": "line",
                 "name": "White", }, ],
                "layout": {"title": "Centipawn Plot", "xaxis_title": "Move Count", "yaxis_title": "Centipawn", }, }

            data = df.to_dict("records")

            return figure, data

        except (json.JSONDecodeError, KeyError):
            return {}, []

    app.run_server(host=host, port=port)


if __name__ == "__main__":
    init_server()
