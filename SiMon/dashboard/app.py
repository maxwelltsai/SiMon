import dash

# meta_tags are required for the app layout to be mobile responsive
import dash_bootstrap_components.themes

app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=[dash_bootstrap_components.themes.LITERA]
                # meta_tags=[{'name': 'viewport',
                #            'content': 'width=device-width, initial-scale=1.0'}]
                )
server = app.server
