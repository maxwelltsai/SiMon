import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pathlib
from SiMon.dashboard import app
import numpy as np
import math


layout = html.Div([
    #Title
    html.Div("Simon Simulation Configuration", style={'text-align':'center', 'font-size': '28px', 'font-weight':'bold' }),
    html.Br(),

    #Second row titles w/ dropdown box
    html.Div([
        html.Div("Initial Conditions", style={
            'text-align':'center',
            'display':'inline-block',
            'width':'50%',
            'vertical-align': 'middle',
            'font-weight': 'bold',
            'font-size': '20px'
        }),
        html.Div("Global configurations: ", style={
            'text-align':'center',
            'display':'inline-block',
            'width':'50%',
            'vertical-align': 'middle',
            'font-weight': 'bold',
            'font-size': '20px'
        }),

    ]),
    html.Br(),

    #Tolerance Exponent + Sim data
    dbc.Row(
        [
            dbc.Col(html.Div("Tolerance Exponent:"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
            dbc.Col(html.Div("Simulation Data Root Directory:"),
                    width={"size": 5, "offset": 1},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                dcc.Input(
                    id="tol_exp",
                    type="text",
                    placeholder="Enter input files list: [ ]",
                    style={
                        'display':'inline-block',
                        'width':'90%',
                    }
                ),
                ),
                style={'padding-left':'30px'},
            ),

            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="root_dir",
                        type="text",
                        placeholder="Enter simulation data root directory:",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
            ),
        ],
    ),

    html.Br(),

    #Length of Word + Time interval
    dbc.Row(
        [
            dbc.Col(html.Div("Length of Word:"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
            dbc.Col(html.Div("Time interval to check all the simulations (in sec) [Default:180]:"),
                    width={"size": 5, "offset": 1},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="length_word",
                        type="text",
                        placeholder="Enter length of word vector: [ ]",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="time_interval",
                        type="text",
                        placeholder="Enter time interval:",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
            ),
        ],
    ),

    html.Br(),

    #Output Time Step + num simulations simultaneously title
    dbc.Row(
        [
            dbc.Col(html.Div("Output Time Step:"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
            dbc.Col(html.Div("The number of simulations to be carried out simultaneously [Default: 2]:"),
                    width={"size": 5, "offset": 1},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="output_time_step",
                        type="text",
                        placeholder="Enter output time step vector: [ ]",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="num_concurrrent_jobs",
                        type="text",
                        placeholder="Enter number of simulations:",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
            ),
        ],
    ),

    html.Br(),

    #Input files + Log level title
    dbc.Row(
        [
            dbc.Col(html.Div("Initial Condition Input Files:"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
            dbc.Col(html.Div("Log level of the daemon: INFO/WARNING/ERROR/CRITICAL [Default: INFO]:"),
                    width={"size": 5, "offset": 1},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="ic_file_list",
                        type="text",
                        placeholder="Enter input files list: [ ]",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="log_level",
                        type="text",
                        placeholder="Enter log level of deamon:",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
            ),
        ],
    ),

    html.Br(),

    #Num obj + Stall time
    dbc.Row(
        [
            dbc.Col(html.Div("Number of objects::"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
            dbc.Col(html.Div("The time in second beyond which a simulation is considered stalled::"),
                    width={"size": 5, "offset": 1},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="num_obj",
                        type="text",
                        placeholder="Enter number of objects: [ ]",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="stall_time",
                        type="text",
                        placeholder="Enter stall time:",
                        style={
                            'display':'inline-block',
                            'width':'90%',
                        }
                    ),
                ),
            ),
        ],
    ),

    html.Br(),

    #Start time
    dbc.Row(
        [
            dbc.Col(html.Div("Starting Time (in sec):"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),

    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="start_time",
                        type="text",
                        placeholder="Enter starting time:",
                        style={
                            'display':'inline-block',
                            'width':'44%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

        ],
    ),

    html.Br(),

    #End time
    dbc.Row(
        [
            dbc.Col(html.Div("End Time (in sec):"),
                    width={"size": 5},
                    style={'padding-left':'60px'}),
        ],
        style={'padding-bottom':'5px'}

    ),
    dbc.Row(
        [
            dbc.Col(
                html.Div(
                    dcc.Input(
                        id="end_time",
                        type="text",
                        placeholder="Enter end time:",
                        style={
                            'display':'inline-block',
                            'width':'44%',
                        }
                    ),
                ),
                style={'padding-left':'30px'},
            ),

        ],
    ),
    html.Br(),

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

    html.Br()


    #Most outer
    ]
)
