import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pathlib
from SiMon.dashboard.app import app
import numpy as np
import math
from SiMon.simulation import Simulation
from SiMon.callback import Callback
from SiMon.simulation_container import SimulationContainer

# num_sim = 25
# simulations = np.arange(0,num_sim)
# list_sim= []
#
# for i in range(simulations.shape[0]):
#     list_sim.append(i+1)
#
# x = []
# y = []
#
# for i in range(num_sim):
#     x_time = np.sort(np.random.randint(low=0, high=15, size=10))
#     y_progress = np.sort(np.random.randint(low=0, high=100, size=10))
#     x_list = x_time.tolist()
#     y_list = y_progress.tolist()
#     x.append(x_list)
#     y.append(y_list)

plot_data = []

def get_dashboard_layout(container):

    layout = html.Div([

        #Title
        html.Div("Simon Simulation Progress", style={'text-align':'center', 'font-size':'28px', 'font-weight':'bold'}, className='Heading 1'),
        html.Br(),

        #Second row titles w/ dropdown box
        html.Div([
            html.Div("All Simulations", style={
                'text-align':'center',
                'display':'inline-block',
                'width':'50%',
                'vertical-align': 'middle',
                'font-size':'20px',
            }),
            html.Div("Simulation: ", style={
                'text-align':'center',
                'display':'inline-block',
                'width':'25%',
                'vertical-align': 'middle',
                'font-size':'20px',
            }),
            html.Div(
                dcc.Dropdown(
                    id='select_sim',
                    options=[{'label': container.sim_inst_dict[i].name, 'value': i} for i in container.sim_inst_dict.keys()],
                    value='0',
                    multi=True,
                ),
                style={
                    'text-align':'center',
                    'display':'inline-block',
                    'width':'20%',
                    'vertical-align': 'middle',
                }),

        ]),

        #Graphs
        #Graph all simulations
        html.Div([
            dcc.Graph(id='all_simulations', figure={})
        ], style={'width': '50%', 'display': 'inline-block'}),

        # html.Img(id='image',style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='one_simulation'),
        ], style={'display': 'inline-block', 'width': '50%'}),


        #Buttons
        html.Div([
            dbc.Button('Run', id='run_button', className='btn-success',
                       style={
                        'margin-right': '20px',
                        'font-size': '15px'
                        }
                       ),
            dbc.Button('Restart', id='restart_button', className='btn-info',
                        style={
                        'margin-right': '20px',
                        'font-size': '15px'
                        }
                       ),
            dbc.Button('Stop', id='stop_button', className='btn-danger',
                        style={
                        'font-size': '15px',
                        }),

        ], style={'text-align':'center'}
        ),

        #Most outer
    ],
        style={'font-family':'Open Sans'})

    return layout


#All simulations graph callback

@app.callback(
    Output(component_id='all_simulations', component_property='figure'),
    # [Input(component_id='container', component_property='dict')]
)


#One simulation graph callback

@app.callback(
    Output(component_id='one_simulation', component_property='figure'),
    [Input(component_id='select_sim', component_property='value'),]
)

def update_one_sim(selected):

    #print(x[int(selected[1])-1])
    #print("selected: {}".format(selected))
    #print("length selected: {}".format(len(selected)))

    for i in range(len(selected)):
        plot_data.append(go.Scatter(x=x[int(selected[i])],
                                    y=y[int(selected[i])],
                                    name = sim_idx[int(selected[i])],
                                    ))


    fig = go.Figure(data=plot_data)

    if len(selected) == 0:
        fig.add_annotation(
            x=0,
            y=4,
            text="Please select simulation(s)",
        )

    plot_data.clear()



    fig.update_layout(
        xaxis = dict(
            tickmode = 'linear',
            tick0 = 0,
            dtick = 1
        ),
        yaxis = dict(
            tickmode = 'linear',
            tick0 = 0,
            dtick = 20
        ),
        xaxis_title="Time (hours)",
        yaxis_title="Progress %",
    )

    return fig
