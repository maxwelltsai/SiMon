import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import config, sim_progress


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(
        [
        dcc.Link('Simulation Progresses |', href='/apps/sim_progress'),
        dcc.Link('Configurations', href='/apps/config'),
    ], className="row", style={'padding-left':'20px'}
        ),
    html.Div(id='page-content', children=[])
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/sim_progress':
        return sim_progress.layout
    if pathname == '/apps/config':
        return config.layout
    else:
        return "404 Page Error! Please choose a link"


if __name__ == '__main__':
    app.run_server(debug=False)