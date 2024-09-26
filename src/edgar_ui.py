import dash, bmt, json, requests, threading, time
from dash import html, dash_table, dcc
from dash_extensions.enrich import Input, Output, callback, State
import dash_bootstrap_components as dbc
import dash_daq as daq
import logging
from src.utils import LoggingUtil
import os

from templates import get_qg
from src.visualization import vizlayout

this_dir = os.path.dirname(os.path.realpath(__file__))

logger = LoggingUtil.init_logging('edgar_dashboard', level=logging.WARNING, format='long', logFilePath=this_dir + '/')


# Global variables to store progress and response
progress = 0
response_data = None
request_in_progress = False
response_status = 0
tk = bmt.Toolkit()
AC_URL = "https://answercoalesce.renci.org/query"
all_node_classes = tk.get_all_classes('entity')


def send_post_request(data):
    global progress, response_data, request_in_progress, response_status
    try:
        request_in_progress = True
        start_time = time.time()  # Record start time
        response = requests.post(AC_URL, json=data)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
        response_data = response.json()
        response_status = response.status_code
        end_time = time.time()  # Record end time
        elapsed_time = end_time - start_time  # Calculate elapsed time
        print(f"Time taken for POST request: {elapsed_time} seconds")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error in send_post_request function: {type(e).__name__}: {str(e)}")
        response_data = f"HTTP error occurred: {e}"
        print(f"HTTP error: {e}")
    except Exception as e:
        logger.error(f"Error in send_post_request function: {type(e).__name__}: {str(e)}")
        response_data = f"Other error occurred: {str(e)}"
        print(f"Error: {e}")
    finally:
        request_in_progress = False
        progress = 100  # Set progress to 100 when done


source = html.Div([
    html.Div(html.B(children='Source Curie')),
    dcc.Input(
        id='source',
        value='',
        type='text',
        placeholder="Leave blank to if this is your \nreturn node(s)...",
        spellCheck="false",
        className='searchTerms'
)])

target = html.Div([
    html.Div(html.B(children='Target Curie:')),
    dcc.Input(
        id='target',
        value='',
        placeholder="Leave blank if this is your \nreturn node(s)...",
        spellCheck="false",
        className='searchTerms'
    )])

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


submit_button = html.Div([
        html.Div([
            dbc.Row(html.Button("Submit Query", id="send-request-button", n_clicks=0)),
            dbc.Row([html.Div([dbc.Col([daq.Gauge(id='progress-gauge', min=0, max=100, value=0), dcc.Interval(id="progress-interval", interval=500, n_intervals=0, disabled=True)]), dbc.Col([dbc.Row([html.Button("Visualize", id="visualize-button", n_clicks=0, className="mr-2", disabled=True)]), dbc.Row([html.Button("Download", id="download-button", n_clicks=0, className="mr-2", disabled=True), dcc.Download(id="download")])])], id="content", style={'display': 'none', 'flex-direction': 'row'})])
        ]),
        dcc.Store(id='response-output-store', data={}),
])


parameters = html.Div([
    dcc.Store(id='parameters-visible', data=False),
    html.Button('Add Parameters?', id='toggle-button', n_clicks=0),
    html.Div(id='parameters-div', style={'background-color': 'whitesmoke', 'display': 'none', 'margin-bottom': '1em'}, children=[dbc.Card([
        dbc.CardHeader("Query Graph Parameters", style={'align-items':'center'}),
        dbc.CardBody([ dbc.Row(children=[dbc.Col(html.Label("P-Value Threshold: ")), dbc.Col(dcc.Input(id='pvalue-threshold', type='number', value=1e-5))]),
            html.Hr(), dbc.Row(children=[dbc.Col(html.Label("Result Length: ")), dbc.Col(dcc.Input(id='result-length', type='number', value=100))]),
            html.Hr(), dbc.Row(children=[dbc.Col(html.Label("Predicates to Exclude (comma-separated): ")), dbc.Col(dcc.Input(id='predicates-to-exclude', type='text', value='causes, biomarker_for, contraindicated_for, contraindicated_in, \ncontributes_to, has_adverse_event, causes_adverse_event, \ntreats_or_applied_or_studied_to_treat', className='smallsearchTerms', style={"width": "100%"}))]),
            html.Button('Submit Params', id='param-submit-button', n_clicks=0, style={"width": "80%", "align": "center"})
        ])
    ], style={'display': 'flex'})]),
    dcc.Store(id = 'param-json-store'),
    html.Div(id='param-output-json', style={'whiteSpace': 'pre-line'})
])


explore_edgar = html.Div([dbc.Container([
                dbc.Collapse([
                    html.Div([
                        html.Tr([
                            html.Div([
                                html.Div([
                                    dcc.Dropdown(
                                        id="example-query-dropdown",
                                        options=[
                                            {'label': "What Drugs treats Disease Y eg. MONDO:0004975?",
                                             'value': "biolink:Drug-biolink:treats-biolink:Disease"},
                                            {'label': "What Genes are genetically associated with Disease X eg. DOID:0050430?",
                                             'value': "biolink:Gene-biolink:genetically_associated_with-biolink:Disease"},
                                            {'label': "What are the Phenotypes of Disease X eg. MONDO:0005147?",
                                                'value': "biolink:Disease-biolink:has_phenotype-biolink:PhenotypicFeature"},
                                            {'label': "What are the Genes that affects Phenotype X eg. HP:0003637?",
                                                'value': "biolink:Gene-biolink:affects-biolink:PhenotypicFeature"},
                                            {'label': "What are the Phenotypes of Gene X eg. NCBIGene:122481?",
                                                'value': "biolink:Gene-biolink:has_phenotype-biolink:PhenotypicFeature"}
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
                        html.Tr(parameters, style={'display':'flex','flex-direction':'row','align-items':'center','justify-content':'center'}),
                    ], className="article-body"),
                    html.Div([html.Div(id="submit-message", style={'display':'flex','flex-direction':'row', 'align-items': 'center', 'justify-content': 'center', 'color':'blue'}), html.Tr(submit_button, style={'padding': '2em', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'justify-content': 'center', 'padding-bottom': '1em', 'background-color': 'whitesmoke', 'border-style': 'outset'})])
                ],
                    id="collapse",
                    is_open=True,
                ),
            ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                html.Div(id='output-data', style={'whiteSpace': 'pre-wrap'})
    ])


####### PARAMETERS CALLBACKS #######################################
@callback( Output('parameters-div', 'style'), Output('submit-message', 'children', allow_duplicate=True), Input('toggle-button', 'n_clicks'), State('parameters-visible', 'data'), State('source', 'value'), State('target', 'value'), State('predicate_dropdown', 'value'))
def param_div_visibility(n_clicks, visible, source_value, target_value, predicate):
    if n_clicks > 0:
        if not (bool(source_value) ^ bool(target_value)) or not (bool(predicate)):
            msg = 'One "biolink" compliant Curie, a return Categories and Predicate is required'
            style = {'color': 'red'}
            return {'display': 'none'}, html.Span(msg, style=style)

        curie = source_value if source_value else target_value

        if not (':' in curie):
            msg = [
                f'{curie} is not "biolink" compliant, e.g., MONDO:0004975',
                html.Br(),
                html.Br(),
                "See ",
                dcc.Link('Name->Curie on the sidebar', href='/normalize_node'),
                " for more details."
            ]
            style = {'color': 'red'}
            return {'display': 'none'}, html.Span(msg, style=style)
        visible = not visible
    return {'display': 'block' if visible else 'none'}, ''


@callback( Output('parameters-visible', 'data'), Input('toggle-button', 'n_clicks'), State('parameters-visible', 'data'))
def update_param_div_visibility(n_clicks, visible):
    if n_clicks > 0:
        return not visible
    return visible


@callback( Output('submit-message', 'children', allow_duplicate=True), Output('param-json-store', 'data'), Input('param-submit-button', 'n_clicks'), State('pvalue-threshold', 'value'), State('result-length', 'value'), State('predicates-to-exclude', 'value'))
def add_parameters(n_clicks, pvalue_threshold, result_length, predicates_to_exclude):
    param_ctx = dash.callback_context
    if not param_ctx.triggered:
        return dash.no_update, dash.no_update

    trigger_id = param_ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == "param-submit-button":
        try:
            predicates_to_exclude_list = [f"biolink:{item.strip()}" for item in predicates_to_exclude.split(',')]
            params = {"parameters":{
                    "pvalue_threshold": pvalue_threshold,
                    "result_length": result_length,
                    "predicates_to_exclude": predicates_to_exclude_list
                    }
            }

            msg = "Params Added!"
            style = {'color': 'blue'}
            return html.Span(msg, style=style), params
        except Exception as e:
            logger.error(f"Error in add_parameters callback: {type(e).__name__}: {str(e)}")
            msg = f"Error: {str(e)}"
            style = {'color': 'red'}
            return html.Span(msg, style=style), dash.no_update


####### TRAPI Query CALLBACKS #######################################
@callback([Output('source_dropdown', 'options'), Output('predicate_dropdown', 'options'), Output('target_dropdown', 'options')], [Input('example-query-dropdown', 'value')])
def update_trapi_component_dropdowns(selected_option):
    if selected_option:
        split_values = selected_option.split('-')
        options_2 = [{'label': split_values[0], 'value': split_values[0]}]
        options_3 = [{'label': split_values[1], 'value': split_values[1]}]
        options_4 = [{'label': split_values[2], 'value': split_values[2]}]
        return options_2, options_3, options_4
    else:
        options = [{'label': option, 'value': option} for option in all_node_classes]
        return options, predicate_temp_options, options


@callback([
        Output("response-output-store", "data"),
        Output("progress-gauge", "value"),
        Output("progress-interval", "disabled"),
        Output("visualize-button", "disabled"),
        Output("download-button", "disabled"),
        Output("download", "data"),
        Output("content", "style"),
        Output("submit-message", "children")
    ],
    Input('param-json-store', 'data'),
    Input("send-request-button", "n_clicks"),
    Input("progress-interval", "n_intervals"),
    Input("visualize-button", "n_clicks"),
    Input("download-button", "n_clicks"),
    [
    State('source', 'value'),
    State('target', 'value'),
    State('source_dropdown', 'value'),
    State('predicate_dropdown', 'value'),
    State('object_aspect_qualifier_dropdown', 'value'),
    State('object_direction_qualifier_dropdown', 'value'),
    State('target_dropdown', 'value')
    ], prevent_initial_call=True
)
def show_json_output(params, n_clicks_send, n_intervals, n_clicks_visualize, n_clicks_download, source_value, target_value, source_category, predicate, object_aspect_qualifier, object_direction_qualifier, target_category):
    global progress, response_data, request_in_progress
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, True, True, True, None, {'display': 'none'}, ''

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "send-request-button":
        if not (bool(source_value) ^ bool(target_value)) or not (bool(predicate)):
            msg = 'One "biolink" compliant Curie and Categories and Predicate is required'
            style = {'color': 'red'}
            return dash.no_update, dash.no_update, True, True, True, None, {'display': 'none'}, html.Span(msg, style=style)

        curie = source_value if source_value else target_value

        if not (':' in curie):
            msg = 'curies must be "biolink" compliant eg MONDO:004975'
            style = {'color': 'red'}
            return dash.no_update, dash.no_update, True, True, True, None, {'display': 'none'}, html.Span(msg, style=style)

        is_source = bool(source_value)
        data = get_qg([curie], is_source, [predicate], source_category, target_category, object_aspect_qualifier, object_direction_qualifier)

        # Validation to check for trapi 'query_graph'
        if "message" not in data or "query_graph" not in data["message"]:
            msg = 'Invalid data format: "message" or "query_graph" key missing'
            style = {'color': 'red'}
            return dash.no_update, dash.no_update, True, True, True, None, {'display': 'none'}, html.Span(msg, style=style)

        progress = 0  # Reset progress
        response_data = None  # Reset response data
        request_in_progress = True  # Mark the request as in progress

        if params:
            data.update(params)

        threading.Thread(target=send_post_request, args=(data,)).start()

        return dash.no_update, 0, False, True, True, None, {'display': 'flex'}, 'Request sent, please wait...'

    elif trigger_id == "progress-interval":
        if request_in_progress:
            # Simulate progress updates while the request is in progress
            simulated_progress = min(progress + 10, 90)  # Let's Cap at 90% until request is done
            progress = simulated_progress
            return dash.no_update, progress, False, True, True, None, dash.no_update, 'Processing, please wait...'
        else:
            # When the request completes
            if progress == 100:
                if response_data and "message" in response_data:
                    return json.dumps(response_data, indent=2), 100, True, False, False, None, dash.no_update, 'Done!'
                else:
                    msg = 'No response available'
                    style = {'color': 'red'}
                    logger.error(f"Error in show_json_output callback: {response_data}")
                    return dash.no_update, 100, True, True, True, None, dash.no_update, html.Span(msg, style=style)

    elif trigger_id == "visualize-button":
        return dash.no_update, dash.no_update, True, False, False, None, dash.no_update, 'Scroll up, visualization in progress...'

    elif trigger_id == "download-button":
        return dash.no_update, dash.no_update, True, False, False, dict(content=json.dumps(response_data, indent=2), filename="response_data.json"), dash.no_update, 'Download ready!'

    return dash.no_update, dash.no_update, True, True, True, None, dash.no_update, dash.no_update  # Default to keeping content hidden


@callback(Output('output-data', 'children', allow_duplicate=True), [Input('response-output-store', 'data'), Input("visualize-button", "n_clicks")])
def visualize_data(store_data, visualize_nclicks):
    if store_data:
        if visualize_nclicks > 0:
            return vizlayout(store_data)
    return ""


@callback(
    Output('output-data', 'children', allow_duplicate=True),
    [Input('example-query-dropdown', 'value'),
     Input('source_dropdown', 'value'),
     Input('predicate_dropdown', 'value'),
     Input('target_dropdown', 'value')]
)
def update_output(selected_query, source_value, predicate_value, target_value):
    return f'Selected Query: {selected_query}, Source: {source_value}, Predicate: {predicate_value}, Target: {target_value}'
