import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pathlib
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
    #Tolerance Exponent + Sim data NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Tolerance Exponent: ", html_for="tol_exp",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="tol_exp", placeholder="Enter input files list: [ ]",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                )
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Simulation Data Root Directory: ", html_for="root_dir",
                                  width=6,
                                  style={'padding-left':'50px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="root_dir", placeholder="Enter simulation data root directory:",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=6,
                        ),
                    ],
                    row=True,
                ),
            ),
        ]
    ),

    html.Br(),

    #Length of Word + Time Stall NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Length of Word: ", html_for="length_word",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="length_word", placeholder="Enter length of word vector: [ ]",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                )
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Stall Time: ", html_for="stall_time",
                                  width=6,
                                  style={'padding-left':'50px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="stall_time", placeholder="Enter stall time:",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=6,
                        ),
                    ],
                    row=True,
                ),
            ),
        ]
    ),

    html.Br(),

    #Output time + Num Sim NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Output Time Step: ", html_for="output_time_step",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="output_time_step", placeholder="Enter output time step",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                )
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("The number of simulations to be carried out simultaneously: ", html_for="num_concurrrent_jobs",
                                  width=8,
                                  style={'padding-left':'50px'}),
                        dbc.Col(
                            dbc.Input(type="number", min=1, max=10, step=1, value=2, id='num_concurrrent_jobs',
                                      style={
                                          'display':'inline-block',
                                          'width':'85%',
                                      }),
                            width=4,
                        ),
                    ],
                    row=True,
                ),
            ),
        ]
    ),

    html.Br(),

    #Initial Conditon + Log Level NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Initial Condition Input Files: ", html_for="ic_file_list",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="ic_file_list", placeholder="Enter input files list: [ ]",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                )
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("The number of simulations to be carried out simultaneously: ", html_for="num_concurrrent_jobs",
                                  width=8,
                                  style={'padding-left':'50px'}),
                        dbc.Col(
                            html.Div(
                                dbc.Select(
                                    id="select",
                                    value='INFO',
                                    bs_size='lg',
                                    options=[
                                        {"label": "INFO", "value": "INFO"},
                                        {"label": "WARNING", "value": "WARNING"},
                                        {"label": "ERROR", "value": "ERROR"},
                                        {"label": "CRITICAL", "value": "CRITICAL"},
                                    ],
                                    style={
                                        'display':'inline-block',
                                        'width':'85%',
                                        'font-size':'18px',
                                    }
                                )
                            ),
                            width=4,
                        ),
                    ],
                    row=True,
                ),
            ),
        ]
    ),

    #Starting time + Time interval NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Starting Time: ", html_for="start_time",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="start_time", placeholder="Enter starting time:",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                ),
                style={'padding-top':'18px'},
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Time interval to check all the simulations (in sec)", html_for="slider",style={'padding-bottom':'10px'}),
                        dcc.Slider(id="time_int", min=0, max=3600, step=10, value=180, tooltip=True,),

                    ],
                    style={
                        'display':'inline-block',
                        'width':'90%',
                        'padding-top':'10px',
                        'padding-left':'50px',
                    },
                    row=True,
                ),
            style={'align-items':'center'},
            ),
        ]
    ),

    html.Br(),

    #Ending time + Dash NEW
    dbc.Row(
        [
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Ending Time: ", html_for="end_time",
                                  width=4,
                                  style={'padding-left':'60px'}),
                        dbc.Col(
                            dbc.Input(
                                type="text", id="end_time", placeholder="Enter ending time:",
                                style={
                                    'display':'inline-block',
                                    'width':'90%',
                                },
                            ),
                            width=8,
                        ),
                    ],
                    row=True,
                )
            ),
            dbc.Col(
                dbc.FormGroup(
                    [
                        dbc.Label("Dashboard + Matplotlib Graph", className='form-check form-switch', style={'padding-left':'35px'}),
                        dbc.Checklist(
                            className='form-check form-switch',
                            options=[
                                {"label": "Dashboard", "value": True},
                                {"label": "Matplotlib Graph", "value": True},
                            ],
                            value=[True],
                            id="switches-input",
                            switch=True,
                            style={'padding-left':'60px', 'align-items':'center'}
                        ),
                    ]
                ),
                #style={'align-items':'center'},
            ),
        ]
    ),

    html.Br(),



    html.Div([
        dbc.Button('Save', id='save_button', className='btn btn-outline-success',
                   color='white',
                   style={
                       'margin-right': '20px',
                       'font-size': '15px',
                   }
                   ),

    ], style={'text-align':'center'}
    ),

    html.Br()


    #Most outer
]
)
