from SiMon.callback import Callback
from SiMon.dashboard.apps import config, sim_progress
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash
import dash_bootstrap_components.themes
import threading 
import numpy as np 
import math 
import plotly.graph_objects as go

class DashboardCallback(Callback):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.__inited = False
        self.app = None  

    def initialize(self):
        if not self.__inited: 
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
                    layout = sim_progress.get_dashboard_layout(container=self.kwargs['container'])
                    print('layout:', layout)
                    return layout
                if pathname == '/apps/config':
                    return config.layout
                else:
                    return "404 Page Error! Please choose a link"

            @self.app.callback(
                Output(component_id='all_simulations', component_property='figure'),
                Input('year-slider', 'value'))
            def update_figure(selected_year):
                self.update_all_sim()

            # threading.Thread(target=self.app.run_server, args=({'debug': False})).start()
            threading.Thread(target=self.app.run_server).start()
            # self.app.run_server(debug=False)
            self.__inited = True 
            
    def update_all_sim(self):
        sim_inst_dict = self.kwargs['container'].sim_inst_dict

        num_sim = len(sim_inst_dict)
        status = np.array([])
        progresses = np.array([])
        sim_idx = np.array([])
        for i, sim_name in enumerate(sim_inst_dict):
            sim = sim_inst_dict[sim_name]
            sim_id = sim.id
            if sim_id == 0:
                continue # skip the root simulation instance, which is only a place holder

            # only plot level=1 simulations
            if sim.level > 1:
                continue

            s = sim.sim_get_status()
            if sim.t_max > 0:
                p = sim.t / sim.t_max
            else:
                p = 0.0
            status = np.append(s, status)
            progresses = np.append(p, progresses)
            sim_idx = np.append(sim_id, sim_idx)

        print(num_sim, progresses)

        # simulations = np.arange(0,num_sim)
        # progresses = np.random.rand(simulations.shape[0])
        # status = np.random.randint(6, size=simulations.shape[0])

        # for i in range(simulations.shape[0]):
        #     list_sim.append(i+1)


        if int(math.sqrt(num_sim) + 0.5) **  2 == num_sim:      #Checks if it has a square
            number = int(math.sqrt(num_sim))

        else:      #If not sqauare
            number = int(math.sqrt(num_sim))
            while num_sim % number != 0:
                number = number - 1      #Find divisible number to get rectangle

            if number == 1:     #If prime number
                number = int(math.sqrt(num_sim)) + 1       #Make sure graph fits all num_sim

        x_sim = sim_idx % number
        y_sim = sim_idx // number

        symbols = ['square', 'triangle-right', 'x',  'triangle-up', 'circle',  'star']
        stat_labels = ['STOP', 'RUN', 'ERROR', 'STALL', 'WARN', 'DONE']

        fig = go.Figure()

        for i, sim_symbol in enumerate(symbols):
            #print(i, sim_symbol),
            fig.add_trace(go.Scatter(
                y = y_sim[status==i],
                x = x_sim[status==i],
                mode='markers',
                showlegend=True,
                name = stat_labels[i],
                hovertemplate = 'Status:',
                marker=dict(
                    size=20,
                    color=progresses, #set color equal to a variable
                    colorscale='Viridis', # one of plotly colorscales
                    colorbar=dict(
                        title='Progress %',
                        tickmode='array',
                        tickvals=[0.05,0.2,0.4,0.6,0.8,0.97],
                        ticktext=['0','20','40','60','80','100']

                    ),

                    showscale=True,
                    symbol = sim_symbol
                )
            )),

        for i in range(sim_idx.shape[0]):
            #fig.update_traces(
            #    hovertemplate = 'Simulation: {sim_num}'.format(sim_num=list_sim[i]),
            #)

            fig.add_annotation(
                x=x_sim[i],
                y=y_sim[i],
                ayref="y",
                ax=0.5,
                ay=2,
                text=str(sim_inst_dict[i].id),
                showarrow=False,
                font=dict(
                    color="white",
                    size=9,
                ),
            )


        fig.update_layout(
            xaxis = dict(
                tickmode = 'linear',
                tick0 = 0,
                dtick = 1
            ),
            yaxis = dict(
                tickmode = 'linear',
                tick0 = 0,
                dtick = 1
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
        )

        return fig


    def run(self):
        print('run1')
        self.initialize()
        print('run2')
        self.update_all_sim() 
        print('run3')
