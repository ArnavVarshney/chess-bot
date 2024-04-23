import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import json

with open("evaluation.json", "r") as f:
    data = json.load(f)

    print(data)

df = pd.DataFrame(data)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("ELEC3442 Chess Bot Analysis", style={"textAlign": "center"}),
        dcc.Graph(
            id="cp-chart",
            figure={
                "data": [
                    {
                        "x": df[df["id"] == "black"]["move_count"],
                        "y": df[df["id"] == "black"]["cp"],
                        "type": "line",
                        "name": "Black",
                    },
                    {
                        "x": df[df["id"] == "white"]["move_count"],
                        "y": df[df["id"] == "white"]["cp"],
                        "type": "line",
                        "name": "White",
                    },
                ],
                "layout": {
                    "title": "Centipawn Plot",
                    "xaxis_title": "Move Count",
                    "yaxis_title": "Centipawn",
                },
            },
        ),
        dash_table.DataTable(
            id="move-table",
            columns=[
                {"name": "Color", "id": "id"},
                {"name": "Move Count", "id": "move_count"},
                {"name": "Best Move", "id": "best_move"},
                {"name": "Time Left (s)", "id": "time_left"},
                {"name": "Centipawn", "id": "cp"},
            ],
            data=df.to_dict("records"),
            style_cell={"textAlign": "center"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        ),
    ], style={"width": "80%", "margin": "auto", "font-family": "Comic Sans MS"}
)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8080)
