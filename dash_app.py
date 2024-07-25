import dash, bmt, json, requests
from dash import callback
import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, Output, Input, State, html, dcc, \
    ServersideOutputTransform

from trapi_qg import get_qg
from byo_data import byo_layout
from viz_module import vizlayout


app = DashProxy(
    __name__,
    pages_folder="",
    transforms=[ServersideOutputTransform()],
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.MATERIA, dbc.icons.FONT_AWESOME, dbc.themes.BOOTSTRAP],
    use_pages=True
)

tk = bmt.Toolkit()
AC_URL = "https://answercoalesce-test.apps.renci.org/query"
all_node_classes = tk.get_all_classes('entity')
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
                    href="/explore_edgar",
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
                    href="/dash_app_byo",
                    active="exact",
                ),

            ],
            vertical=True,
            pills=True,
        ),
    ], className="sidebar")

source = html.Div([
    html.Div(html.B(children='Source Curie')),
    dcc.Input(
        id='source',
        value='',
        type='text',
        placeholder="Leave blank to if this is your return node(s)...",
        spellCheck="false",
        className='searchTerms'
)])

target = html.Div([
    html.Div(html.B(children='Target Curie:')),
    dcc.Input(
        id='target',
        value='',
        placeholder="Leave blank if this is your return node(s)...",
        spellCheck="false",
        className='searchTerms'
    )])

def search_query(message):
    response = requests.post( AC_URL, json = message )
    print(response.status_code)
    if response.status_code == 200:
        return response.json()
    return message


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


@callback(Output('curie-output', 'children'), [Input('searchname', 'value'), Input('submit-name', 'n_clicks')])
def normalizeterm(searchterm, click):
    if click > 0 and searchterm:
        curie = resolvename(searchterm)
        res = curie + ' Please Double Check!' if curie else 'Unknown'
        return """Most Probable Curie: {} """.format(res)


############################
query_clipboard = dcc.Clipboard(
        id="clipboard-button",
        title="Copy Neo4j Queries",
        style={"display": "inline-block", "fontSize": 20, "verticalAlign": "top"})


robokop_link = html.A(
    id = "robokop-link",
    children=html.Img(src='/assets/robokop.png',style={'height':'2em','width':'6em','padding-left':'1em'}),
    href='https://robokop.renci.org/',
    target='_blank',
    rel='noopener noreferrer')


submit_button = html.Div(children=[
        html.Button('Submit Query Graph', id='trapi-submit-button', n_clicks=0),
        html.Div(id='trapi-output-container-button', children='Enter the values and press submit to make inference'),
        html.Div(id='json-trapi-output', style={'display': 'none'}),
        # query_clipboard,
        robokop_link], style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'})

@callback(Output("download-trapi-results", "data"), Input('json-trapi-output', 'data'), Input("result-btn", "n_clicks"), prevent_initial_call=True)
def func(n_clicks, json_results):
    if n_clicks:
        return dcc.send_data_frame(json_results.to_json, "response.json")

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
                    "By utilizing enrichment-driven analyses on KG data from ROBOKOP, this study focuses on repurposing drug candidates for Alzheimer's disease, demonstrating the efficacy of enrichment strategies in linking entities for drug discovery. Our approach is validated through literature-based evidence derived from clinical trials, showcasing the potential of enrichment-driven strategies in linking biomedical entities."
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

parameters = html.Div([
    dcc.Store(id='parameters-visible', data=False),
    html.Button('Add Parameters?', id='toggle-button', n_clicks=0),
    html.Div(id='parameters-div', style={'background-color': 'whitesmoke', 'display': 'none', 'margin-bottom': '1em'},
             children=[dbc.Card([dbc.CardHeader("Question Graph Parameters"),
                              dbc.CardBody([
                                dbc.Row(children=[dbc.Col([dbc.Col(html.Label("P-Value Threshold")), dbc.Col(dcc.Input(id='pvalue-threshold', type='number', value=1e-7))])]),
                                dbc.Row(children=[dbc.Col([html.Label("Result Length"), dcc.Input(id='result-length', type='number', value=100)])]),
                                dbc.Row(children=[dbc.Col(html.Label("Predicates to Exclude (comma-separated)")),
                                    dbc.Col(html.Label("Node Set to Exclude (comma-separated)"))]),
                                dbc.Row(children=[dbc.Col(dcc.Input(id='predicates-to-exclude', type='text', value=f'causes, \nbiomarker_for, \ncontraindicated_for, \ncontraindicated_in, \ncontributes_to, \nhas_adverse_event, \ncauses_adverse_event, \ntreats_or_applied_or_studied_to_treat', className='smallsearchTerms'))]),
                                html.Button('Submit', id='param-submit-button', n_clicks=0)
                              ])
                        ], style={'display': 'flex'})
                    ]),
    dcc.Store(id = 'param-json-store'),
    html.Div(id='param-output-json', style={'whiteSpace': 'pre-line'})
])

explore_edgar = dbc.Container([
                dbc.Collapse([
                    html.Div([
                        html.Tr([
                            html.Div([
                                html.Div([
                                    dcc.Dropdown(
                                        id="example-query-dropdown",
                                        options=[
                                            {'label': "What Drugs treats Disease Y?",
                                             'value': "biolink:Drug-biolink:treats-biolink:Disease"},
                                            {'label': "What Genes is associated with Disease X?",
                                             'value': "biolink:Gene-biolink:associated_with-biolink:Disease"},
                                            {'label': "What are the Biological Process and Molecular Activities that affects Genes X?",
                                                'value': "biolink:BioProcessOrActivity-biolink:affects-biolink:Gene"}
                                        ],
                                        value=None,
                                        placeholder='Select an example query pattern...optional',
                                        multi=False,
                                        clearable=True
                                    ),
                                ],
                                    id="example-query-div",
                                    className='dropdownbox',
                                    style={'width': '50em', 'margin-bottom': '1em', 'line-height': '1em', 'font-size': '100%', }
                                ),
                            ],
                                style={'background-color': 'whitesmoke', 'display': 'flex', 'flex-direction': 'row',
                                       'align-items': 'center',
                                       'justify-content': 'center'}
                            ),
                            html.Div(style={'padding-bottom': '3em', 'vertical-align': 'top'},
                                     children=[
                                         html.Td([
                                             html.H2('Source Type:'),
                                             dcc.Dropdown(id='source_dropdown', className='dropdownbox',
                                                          placeholder='Select Source Node Type...', clearable=False),
                                             html.Div([source], style={'display': 'flex', 'flex-direction': 'row',
                                                                       'align-items': 'center',
                                                                       'justify-content': 'left'}),
                                         # load_start,
                                         ], style={'width': '15em', 'padding-right': '1em'}),
                                         html.Td([
                                             html.H2('Predicates:'),
                                             dcc.Dropdown(id='predicate_dropdown', className='dropdownbox',
                                                          placeholder='Select Predicate...', clearable=False),
                                             html.Div([
                                                 html.H3('Object_aspect_qualifier:'),
                                                dcc.Dropdown(id='object_aspect_qualifier_dropdown', className='dropdownbox',
                                                          placeholder='object_aspect_qualifier...', clearable=False),

                                                 html.H3('Object_direction_qualifier:'),
                                                 dcc.Dropdown(id='object_direction_qualifier_dropdown', className='dropdownbox',
                                                          placeholder='Select object_direction_qualifier...', clearable=False),
                                             ]),
                                             dbc.Row([
                                                 dbc.Col(parameters),
                                                 dbc.Col([
                                                     html.Button('View Trapi', id='qg-submit-button', n_clicks=0),
                                                     html.Div(id='output-container-button', children='Enter the values and press submit to view the Query_Graph'),
                                                     html.Div(id='json-output', style={'display': 'none'})
                                                 ])
                                             ])
                                         ], style={'width': '15em', 'padding-right': '1em'}),
                                         html.Td([
                                             html.H2(children='Target Type:'),
                                             dcc.Dropdown(id='target_dropdown', className='dropdownbox',
                                                          placeholder='Select Target Node Type...', clearable=False),
                                             html.Div([target], style={'display': 'flex', 'flex-direction': 'row',
                                                                       'align-items': 'center',
                                                                       'justify-content': 'right'}),

                                         ], style={'width': '15em', 'padding-left': '1em'}),
                                     ])
                        ]),
                        html.Tr([
                            html.Div([
                                submit_button], style={'padding': '2em', 'display': 'flex', 'flex-direction': 'column',
                                                 'align-items': 'center', 'justify-content': 'center',
                                                 'padding-bottom': '1em', 'background-color': 'whitesmoke',
                                                 'border-style': 'outset'}),

                        ]),
                    ], className="article-body")
                ],
                    id="collapse",
                    is_open=True,
                )
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'})

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
                    html.Div('Enrichment-Driven GrAph Recommender (EDGAR)',
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


####### PARAMETERS CALLBACKS #######################################

# Callback for the parameters div visibility
@app.callback( Output('parameters-div', 'style'), Input('toggle-button', 'n_clicks'), State('parameters-visible', 'data'))
def add_parameters(n_clicks, visible):
    if n_clicks > 0:
        visible = not visible
    return {'display': 'block' if visible else 'none'}

# Callback to update the store
@app.callback( Output('parameters-visible', 'data'), Input('toggle-button', 'n_clicks'), State('parameters-visible', 'data'))
def update_store(n_clicks, visible):
    if n_clicks > 0:
        return not visible
    return visible

@app.callback( Output('param-json-store', 'data'), Input('param-submit-button', 'n_clicks'), State('pvalue-threshold', 'value'),
               State('result-length', 'value'), State('predicates-to-exclude', 'value'))
def update_output(n_clicks, pvalue_threshold, result_length, predicates_to_exclude):
    if n_clicks > 0:
        try:
            predicates_to_exclude_list = [f"biolink:{item.strip()}" for item in predicates_to_exclude.split(',')]
            # nodeset_to_exclude_list = [f"biolink:{item.strip()}" for item in nodeset_to_exclude.split(',')]
            params = {"parameters":{
                    "pvalue_threshold": pvalue_threshold,
                    "result_length": result_length,
                    "predicates_to_exclude": predicates_to_exclude_list
                    # "nodeset_to_exclude": nodeset_to_exclude_list
                    }
            }
            html.Div("Params Added!")
            return params
        except Exception as e:
            return f"Error: {e}"
    return "Enter parameters and click submit."

predicate_temp_options = ['biolink:treats', 'biolink:affects', 'biolink:regulates',
'biolink:associated_with', 'biolink:active_in', 'biolink:actively_involved_in',
'biolink:acts_upstream_of','biolink:acts_upstream_of_negative_effect',
'biolink:acts_upstream_of_or_within_negative_effect',
'biolink:acts_upstream_of_or_within_positive_effect',
'biolink:acts_upstream_of_positive_effect',
'biolink:affects_response_to',
'biolink:ameliorates',
'biolink:associated_with',
'biolink:binds',
'biolink:capable_of',
'biolink:catalyzes',
'biolink:causes',
'biolink:coexists_with',
'biolink:coexpressed_with',
'biolink:colocalizes_with',
'biolink:composed_primarily_of',
'biolink:contraindicated_for',
'biolink:contributes_to',
'biolink:correlated_with',
'biolink:decreases_response_to',
'biolink:derives_from',
'biolink:develops_from',
'biolink:directly_physically_interacts_with',
'biolink:disease_has_basis_in',
'biolink:disrupts',
'biolink:expressed_in',
'biolink:gene_associated_with_condition',
'biolink:gene_product_of',
'biolink:genetically_associated_with',
'biolink:genetically_interacts_with',
'biolink:has_adverse_event',
'biolink:has_input',
'biolink:has_output',
'biolink:has_part',
'biolink:has_participant',
'biolink:has_phenotype',
'biolink:homologous_to',
'biolink:in_taxon',
'biolink:increases_response_to',
'biolink:is_frameshift_variant_of',
'biolink:is_missense_variant_of',
'biolink:is_nearby_variant_of',
'biolink:is_non_coding_variant_of',
'biolink:is_nonsense_variant_of',
'biolink:is_splice_site_variant_of',
'biolink:is_synonymous_variant_of',
'biolink:located_in',
'biolink:negatively_correlated_with',
'biolink:occurs_in',
'biolink:overlaps',
'biolink:physically_interacts_with',
'biolink:positively_correlated_with',
'biolink:precedes',
'biolink:produces',
'biolink:regulates',
'biolink:related_to',
'biolink:similar_to',
'biolink:subclass_of']

@app.callback(
    [Output('source_dropdown', 'options'), Output('predicate_dropdown', 'options'),
     Output('target_dropdown', 'options')],
    [Input('example-query-dropdown', 'value')]
)
def update_dropdowns(selected_option):
    if selected_option:
        split_values = selected_option.split('-')
        options_2 = [{'label': split_values[0], 'value': split_values[0]}]
        options_3 = [{'label': split_values[1], 'value': split_values[1]}]
        options_4 = [{'label': split_values[2], 'value': split_values[2]}]
        return options_2, options_3, options_4
    else:
        options = [{'label': option, 'value': option} for option in all_node_classes]
        return options, predicate_temp_options, options

@app.callback(
    [Output('json-output', 'children'),
     Output('output-container-button', 'children'),
     Output('json-trapi-output', 'children'),
     Output('trapi-output-container-button', 'children')
     ],
    [Input('param-json-store', 'data'), Input('qg-submit-button', 'n_clicks'), Input('trapi-submit-button', 'n_clicks')],
    [State('source', 'value'),
     State('target', 'value'),
     State('source_dropdown', 'value'),
     State('predicate_dropdown', 'value'),
     State('object_aspect_qualifier_dropdown', 'value'),
     State('object_direction_qualifier_dropdown', 'value'),
     State('target_dropdown', 'value')]
)
def show_json_output(params, qg_n_clicks, infer_n_clicks, source_value,  target_value, source_category, predicate, object_aspect_qualifier, object_direction_qualifier, target_category):
    if qg_n_clicks > 0 or infer_n_clicks > 0:
        if not source_value and target_value:
            if (not source_value or ':' in source_value) and (not target_value or ':' in target_value):
                if source_value:
                    is_source = True
                    curie = source_value
                else:
                    is_source = False
                    curie = target_value
                json_trapi = get_qg([curie], is_source, [predicate], source_category, target_category,  object_aspect_qualifier, object_direction_qualifier)
                message = {"message": json_trapi}
                if params:
                    message.update(params)
                print('json_status: ', message)
                if qg_n_clicks > 0:
                    return json.dumps(json_trapi, indent=4), html.Div(
                            [
                                dbc.Button("Open Query", id="open"),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Input Query Graph"),
                                        dbc.ModalBody(html.Pre(json.dumps(json_trapi, indent=4), id='pre')),
                                        dbc.ModalFooter([dcc.Clipboard( target_id="pre", title="copy", style={ "position": "absolute", "bottom": 5, "left": 20, "fontSize": 20,  "verticalAlign": "bottom", 'color': 'blue' }),
                                            dbc.Button("CLOSE", id="close", className="ml-auto")]
                                        ),
                                    ],
                                    id="modal",
                                ),
                            ],
                        style={"max-width": "none", "width": "50%"}
                        ), '', ''
                if infer_n_clicks > 0:
                    debug_message = 'we are here!!'
                    edgar_url = "https://answercoalesce-test.apps.renci.org/query"
                    response = requests.post(edgar_url, json=message)
                    if response.status_code == 200:
                        dbc.Alert("Query successfull!", color="success"),
                        json_output = response.json()
                        return '', '', vizlayout(json_output), html.Div(debug_message)
                    else:
                        dbc.Alert(f"Error: {response.status_code}!", color="danger"),
                        json_output = json_trapi
                    print('json_status: ', response.status_code)
                    print('json_status: ', message)
                    return '', '', json.dumps(json_output, indent=4), html.Div(
                        [
                            dbc.Button("View Trapi Result", id="opentrapiresult"),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader("Trapi Result"),
                                    dbc.ModalBody(
                                        html.Pre([json.dumps(json_output, indent=4)], id='pre2')
                                    ),
                                    dbc.ModalFooter(
                                        [html.Button('Download Result', id='result-btn'),
                                         dcc.Download(id="download-trapi-results"),
                                         dbc.Button("CLOSE", id="close", className="ml-auto")]
                                    ),
                                ],
                                id="modal1",
                            ),
                            html.Div(debug_message)
                        ],
                        style={"max-width": "none", "width": "50%"}
                    ),
            else:
                if qg_n_clicks > 0:
                    return '', html.Div('Curie must be empty or be "biolink" compliant'), '', ''
                else:
                    return '', '', '', html.Div('Curie must be empty or be "biolink" compliant')

        else:
            if qg_n_clicks:
                return '', html.Div('One "biolink" compliant Curie and Categories and Predicate is required'), '', ''
            else:
                return '', '', '', html.Div('One "biolink" compliant Curie and Categories and Predicate is required')

    return '', '', '', ''#'Enter the values to view the QG'

#NAvBar callbacks
@app.callback(Output("page-content", "children"),
              [Input('url', 'pathname')],
             )
def display_content(pathname):
    if pathname == "/dash_app_byo":
        # app.clientside_callback(
        #     """
        #     function(id) {
        #         return `<!DOCTYPE html><meta charset="utf-8">${id}`
        #     }
        #     """,
        #     Output("my_dataviz", "children", allow_duplicate=True),
        #     [Input("my_dataviz", "id")],
        # )

        return byo_layout
    elif pathname == "/explore_edgar":
        return explore_edgar
    elif pathname == "/normalize_node":
        return normalize_node
    else:
        return about


@app.callback( [Output("modal", "is_open"), Output("open", "n_clicks")],
    [Input("open", "n_clicks"), Input("close", "n_clicks")], [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if "close" in changed_id:
        return False, {"display": "none"}

    if n1 or n2:
        return not is_open, {}

    return is_open, {}


if __name__ == "__main__":
    app.run_server(debug=True)
