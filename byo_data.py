import json, base64
from dash import dcc, html
from dash_extensions.enrich import Input, Output, callback, State
import dash_bootstrap_components as dbc
from viz_module import vizlayout


@callback(Output('store-response', 'data'), [Input('upload-data', 'contents')], [State('upload-data', 'filename')])
def load_data(contents, filename):
    if contents is not None and filename.endswith('.json'):
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        response = json.loads(decoded)
        return response
    return ''

# Define callback to display the loaded JSON data
@callback(Output('output-data', 'children'), [Input('store-response', 'data')])
def display_data(store_data):
    if store_data:
        return vizlayout(store_data)
    return html.Div("No data loaded")

#
byo_layout = dbc.Container([
            html.Div([
                dcc.Upload( id='upload-data', children=[html.Button('Drag and Drop or Select Files',style = {'width': '100%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'position': 'relative', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})],
                        multiple=False,
                        accept='.json'
                ),
            ]),
            dcc.Store(id='store-response'),
            html.Div(id='output-data', style={'whiteSpace': 'pre-wrap'})
        ],
        fluid=True,
        style={"overflow": "auto",}
)

