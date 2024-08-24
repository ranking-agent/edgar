import json
import base64
import logging
from src.utils import LoggingUtil
import os
from dash import dcc, html
from dash_extensions.enrich import Input, Output, callback, State
import dash_bootstrap_components as dbc
from src.visualization import vizlayout


this_dir = os.path.dirname(os.path.realpath(__file__))

logger = LoggingUtil.init_logging('bring_your_own_data', level=logging.WARNING, format='long', logFilePath=this_dir + '/')


# Callback to load data
@callback(Output('store-response', 'data'), [Input('upload-data', 'contents')], [State('upload-data', 'filename')])
def load_data(contents, filename):
    if contents is not None and filename.endswith('.json'):
        try:
            _, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            response = json.loads(decoded)
            logger.info(f"JSON data Decoded")
            return response
        except Exception as e:
            logger.error(f"Error decoding or parsing JSON: {type(e).__name__}: {str(e)}")
            return ''
    logger.info("No contents provided or incorrect file type")
    return ''


# callback to display the loaded JSON data
@callback(Output('output-data', 'children'), [Input('store-response', 'data')])
def display_data(store_data):
    if store_data:
        result = vizlayout(store_data)
        logger.info(f"Data uploaded!")
        return result 
    logger.info("No data loaded to display")
    return html.Div("No data loaded")


# callback to view sample result
@callback(Output('output-data', 'children', allow_duplicate=True), [Input('sample-result', 'n_clicks')])
def sample_data(n_clicks):
    if n_clicks > 0:
        try:
            with open("src/samples/MONDO0004975Drug.json", "r") as inf:
                response = json.load(inf)
            result = vizlayout(response)
            logger.info(f"Data loaded!")
            return result
        except Exception as e:
            logger.error(f"Error decoding or parsing JSON: {type(e).__name__}: {str(e)}")
            return ''
    return ''


byo_layout = dbc.Container([
            dbc.Row([dbc.Col(html.Div([
                dcc.Upload(id='upload-data', children=[html.Button('Select a json File', style={'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'position': 'relative', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})],
                           multiple=False,
                           accept='.json'
                ),
            ])), dbc.Col(html.Div([html.Button('View Alzheimer Sample', id = 'sample-result', n_clicks=0, style={'width': '90%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'position': 'relative', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})]))]),
            dcc.Store(id='store-response'),
            html.Div(id='output-data', style={'whiteSpace': 'pre-wrap'})
        ],
        fluid=True,
        style={"overflow": "auto",}
)
