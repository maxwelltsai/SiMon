from SiMon.callback import Callback
from SiMon.dashboard.apps import config, sim_progress
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash
import dash_bootstrap_components.themes

class DashboardCallback(Callback):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.__inited = False
        self.app = None  

    def initialize(self):
        if not self.__inited: 
            print('jkdsfhjksdhgkjdahglkadh')
            # launch the dashboard entry point 
            self.app = dash.Dash(__name__, suppress_callback_exceptions=True,
                            external_stylesheets=[dash_bootstrap_components.themes.LITERA]
                            # meta_tags=[{'name': 'viewport',
                            #            'content': 'width=device-width, initial-scale=1.0'}]
                            )
            server = self.app.server
            self.app.layout = html.Div([
                dcc.Location(id='url', refresh=False),
                html.Div(
                    [
                    dcc.Link('Simulation Progresses |', href='/apps/sim_progress'),
                    dcc.Link('Configurations', href='/apps/config'),
                ], className="row", style={'padding-left':'20px'}
                    ),
                html.Div(id='page-content', children=[])
            ])

            @self.app.callback(Output('page-content', 'children'), [Input('url', 'pathname')])
            def display_page(pathname):
                if pathname == '/apps/sim_progress':
                    return sim_progress.layout
                if pathname == '/apps/config':
                    return config.layout
                else:
                    return "404 Page Error! Please choose a link"

            self.app.run_server(debug=False)
            self.__inited = True 
            


    def run(self):
        self.initialize()
        sim_progress.update_all_sim(self.kwargs['container']) 
