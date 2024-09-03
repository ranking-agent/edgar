import dash, json, requests
from dash import callback, callback_context
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, Output, Input, State, html, dcc, \
    ServersideOutputTransform

from src.edgar_ui import explore_edgar
from src.bring_your_own_data import byo_layout


app = DashProxy(
    __name__,
    pages_folder="",
    transforms=[ServersideOutputTransform()],
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MATERIA, dbc.icons.FONT_AWESOME, dbc.themes.BOOTSTRAP],
    use_pages=True
)

server = app.server


robokop_link = html.A(
    id = "robokop-link",
    children=html.Img(src='/assets/robokop.png',style={'height':'2em','width':'6em','padding-left':'1em'}),
    href='https://robokop.renci.org/',
    target='_blank',
    rel='noopener noreferrer')


colors = {'background': 'white', 'background': '#7794B8', 'dropdown': '#6c6f73', 'text': '#000000'}


sidebar = html.Div([
        html.Div(
            [
                html.H2("EDGAR", style={"color": "#0096FF"}),
            ],
            className="sidebar-header",
        ),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-home me-2"), html.Span("Home")],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fa-solid fa-chart-line"),
                        html.Span("EDGAR Dashboard"),
                    ],
                    id='home-link',
                    href="/edgar_dashboard",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fa-solid fa-check-double"),
                        html.Span(" Name->Curie"),
                    ],
                    id='curie-link',
                    href="/normalize_node",
                    active="exact",
                ),
                dbc.NavLink(
                    [
                        html.I(className="fa-solid fa-database"),
                        html.Span("BYO Datasets"),
                    ],
                    id='byo-link',
                    href="/byo_response_data",
                    active="exact",
                ),

            ],
            vertical=True,
            pills=True,
        ),
    ], className="sidebar")


############# Normalization ########################
def resolvename(name):
    name_resolver_url = f'https://name-resolution-sri.renci.org/lookup?string={name}&offset=0&limit=2'
    res = requests.post(name_resolver_url).json()
    curie = ''
    for rs in res:
        if rs['label']==name or rs['label'].lower() == name.lower():
            curie = rs['curie']
            break
    return curie


about = dbc.Container([
    html.Div([
        html.Div(
            html.H3(
                ['Summary'],
                style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}
            )
        ),
        html.Hr(),
    ],
        style={'background-color': 'whitesmoke', 'display': 'flex', 'flex-direction': 'row',
               'align-items': 'center', 'justify-content': 'center'}
    ),
    html.Br(),
    html.Div([
            html.Div(
                html.Article([
                    "This research explores pathway enrichment strategies in biomedical Knowledge Graphs (KGs) as a versatile link-prediction approach, with drug repurposing exemplifying a significant application. Leveraging systems biology, network expression analysis, pathway analysis (PA), and machine learning (ML) methods, KGs aid in uncovering novel interactions among biomedical entities of interest. ",
                    html.P(),
                    "While these approaches excel in inferring missing edges within the KG, PA may overlook candidates with similar pathway effects. ",
                    html.P(),
                    "By utilizing enrichment-driven analyses on KG data from ROBOKOP, our EDGAR paper applied this method on Alzheimer's disease case study, demonstrating the efficacy of enrichment strategies in linking entities for drug repurposing. Our approach is validated through literature-based evidence derived from clinical trials, showcasing the potential of enrichment-driven strategies in linking biomedical entities."
                ],
                    style={'font-size': '20px'}
                )
            ),
            html.Br(),
            html.Div(
                robokop_link
            )

        ],
            style={'background-color': 'whitesmoke', 'display': 'flex', 'flex-direction': 'row',
                   'align-items': 'center', 'justify-content': 'center'}
    ),
], className="p-3 bg-body-secondary rounded-3")


normalize_node = dbc.Container([
                dbc.Collapse([
                    html.Div([
                        html.Tr([
                            html.Div(style={'padding-bottom': '3em', 'vertical-align': 'top'},
                                     children=[
                                         html.Td([
                                             html.H2('Get Normalized Node:'),
                                             html.Div([
                                                 dcc.Input(id='searchname', value='', placeholder='Headache',
                                                           type='text'),
                                                 html.Button('Get Curie', id='submit-name', n_clicks=0),
                                                 html.Div(id='curie-output'),
                                                 dcc.Clipboard(
                                                    target_id="curie-output",
                                                    title="copy",
                                                    style={
                                                        "position": "absolute",
                                                        "bottom": 5,
                                                        "left": 20,
                                                        "fontSize": 20,
                                                        "verticalAlign": "top",
                                                        'color': 'blue'
                                                    },
                                                 ),
                                             ])
                                         ], style={'width': '15em', 'padding-right': '1em'}),

                                     ])
                        ]),
                    ], className="article-body")
                ],
                    id="collapse",
                    is_open=True,
                )
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})


def page_container():
    return html.Div(
        children=[
            html.H1(children=[
                html.Div([
                    html.Div('Enrichment-Driven GrAph Reasoner (EDGAR)',
                             style={'font-size': '40px', 'align-items': 'center', 'justify-content': 'center'})]),
                ],
                    style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'justify-content': 'center',
                            "color": "#0096FF", 'background-color': '#cbd3dd', 'width': '100%'}
            ),
            html.Div([

            ],
            id = 'page-content',
            style={'padding-left': '6rem'}
            )
        ],
    className='page-bg')


app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        sidebar,
        page_container(),
    ]
)

####### NAVBAR CALLBACKS #######################################
@app.callback(Output("page-content", "children"), [Input('url', 'pathname')])
def display_content(pathname):
    if pathname == "/byo_response_data":
        return byo_layout
    elif pathname == "/edgar_dashboard":
        return explore_edgar
    elif pathname == "/normalize_node":
        return normalize_node
    else:
        return about


@app.callback( [Output("modal", "is_open"), Output("open", "n_clicks")], [Input("open", "n_clicks"), Input("close", "n_clicks")], [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "close" in changed_id:
        return False, {"display": "none"}

    if n1 or n2:
        return not is_open, {}

    return is_open, {}


####### NameResolver CALLBACK #######################################
@app.callback(Output('curie-output', 'children'), [Input('searchname', 'value'), Input('submit-name', 'n_clicks')])
def normalizeterm(searchterm, click):
    if click > 0 and searchterm:
        curie = resolvename(searchterm)
        if curie:
            message = html.Div([
                html.Span(f'Most Probable Curie: {curie} ', style={'color': 'blue'}),
                html.Br(),
                html.Span('Please Double Check!', style={'color': 'blue'}),
            ])
        else:
            message = html.Span('Sorry! curie not known', style={'color': 'red'})
        return message
    return "This module accepts string entity name and return biolink compliant curie"


#### Visualize the Output ######
if __name__ == "__main__":
    app.run_server(debug=False)
