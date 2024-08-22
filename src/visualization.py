import pandas as pd
import orjson
from io import StringIO
from dash import html, dash_table, dcc
from dash_extensions.enrich import Input, Output, callback, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import os
import logging
from src.utils import LoggingUtil

this_dir = os.path.dirname(os.path.realpath(__file__))

logger = LoggingUtil.init_logging('visualization', level=logging.WARNING, format='long', logFilePath=this_dir + '/')


color_palette = [
    "#33FF57",  # bright green
    "#FF33A1",  # hot pink
    "#A133FF",  # purple
    "#8A33FF",  # violet
    "#FF33D4",  # magenta
    "#33FFD4",  # turquoise
    "#FFD433",  # yellow
    "#FF5733",  # orange
    "#33A1FF",  # sky blue
    "#FF3333",  # red
    "#FF338A",  # fuchsia
    "#FF33FF",  # pink
    "#33D4FF",  # cyan
    "#FF8A33",  # pumpkin orange
]


custom_conditional_style = [
    {
        'if': {'state': 'active'},  # clicked on
        'backgroundColor': 'rgba(0, 116, 217, 0.3)',
        'border': '1px solid rgb(0, 116, 217)',
        'whiteSpace': 'normal',  # To ensure text wraps
        'height': 'auto',
    },
    {
        'if': {'column_id': 'Source_'},
        'backgroundColor': 'rgb(248, 248, 248)',
        'color': 'black'
    },
    {
        'if': {'column_id': 'Predicate_'},
        'backgroundColor': 'rgb(220, 220, 220)',
        'color': 'black'
    },
    {
        'if': {'column_id': 'Target_'},
        'backgroundColor': 'rgb(210, 210, 210)',
        'color': 'black'
    },
    {
        'if': {'column_id': 'EdgeString_'},
        'backgroundColor': 'rgb(210, 210, 210)',
        'color': 'black'
    },
    {
        'if': {
            'column_id': 'Source'
        },
        'color': '#33D4FF',
        'fontWeight': 'bold'
    },
    {
        'if': {
            'column_id': 'Object1'
        },
        'color': '#33D4FF',
        'fontWeight': 'bold'
    },
    {
        'if': {
            'column_id': 'Subject1'
        },
        'color': '#33D4FF',
        'fontWeight': 'bold'
    },
    {
        'if': {
            'column_id': 'Target'
        },
        'color': '#FF5733',
        'fontWeight': 'bold'
    },
    {
        'if': {
            'column_id': 'Object2'
        },
        'color': '#FF5733',
        'fontWeight': 'bold'
    },
]


def get_answer_components(answerset):
    query_graph = answerset["message"]["query_graph"]
    kg_edges = answerset["message"]["knowledge_graph"]["edges"]
    kg_nodes = answerset["message"]["knowledge_graph"]["nodes"]
    results = answerset["message"]["results"]
    aux_graphs = answerset["message"]["auxiliary_graphs"]
    return query_graph, kg_edges, kg_nodes, results, aux_graphs


def get_inferred_result_df( kg_edges, kg_nodes, results ):
    inferences = [edge[0]['id'] for result in results for _, edge in result["analyses"][0]["edge_bindings"].items()]
    inference_list = [[kg_edges[inferred_edge]["subject"], kg_nodes[kg_edges[inferred_edge]["subject"]]["name"],
                       kg_edges[inferred_edge]["predicate"],
                       kg_nodes[kg_edges[inferred_edge]["object"]]["name"], inferred_edge] for inferred_edge in
                      inferences]

    df = pd.DataFrame(inference_list, columns=["Source_ID", "Source", "Predicate", "Target", "EdgeString"])

    support_graphs = [[attributes["value"] for attributes in kg_edges[inference_edge]["attributes"] if
                       attributes["attribute_type_id"] == "biolink:support_graphs"] for inference_edge in inferences]
    method_mapping = [', '.join({"graph" if support[0] == 'e' else 'property' for support in supports}) for supports in
                      support_graphs]
    df["Enrichment_method"] = method_mapping
    return df


def get_all_node_categories(kg_nodes):
    node_categories = list({kg_node["categories"][0] for kg_node in kg_nodes.values()})
    return node_categories


def generate_color_map(categories, palette=color_palette):
    fixed_colors = {
        "biolink:Disease": "#FF5733",
        "biolink:NamedThing": "#FF5733",
        "biolink:ChemicalEntity": "#33D4FF",
        "biolink:Drug": "#33D4FF",
        "biolink:ChemicalRole": "#33D4FF",
    }

    dynamic_categories = [category for category in categories if category not in fixed_colors]

    unique_palette = palette[:]
    while len(unique_palette) < len(dynamic_categories):
        unique_palette.extend(palette)

    dynamic_colors = {category: unique_palette[i] for i, category in enumerate(dynamic_categories)}

    return {**fixed_colors, **dynamic_colors}


def get_node_color( category_colors, category ):
    return category_colors.get(category, "#CCCCCC")


def get_node_shape( node_categories, category ):
    shapes = ['ellipse', 'triangle', 'rectangle', 'round-rectangle', 'diamond', 'pentagon', 'hexagon', 'heptagon',
              'octagon']
    return shapes[node_categories.index(category) % len(shapes)]


def display_qg( query_graph ):
    nodes = []
    edges = []
    for node, node_dict in query_graph["nodes"].items():
        if node_dict.get('ids'):
            abackground_color = '#FF5733'
            q_node_ids = node_dict.get('ids')
            nodes.append({'data': {'id': q_node_ids[0], 'label': q_node_ids[0]},
                          'style': {'background-color': abackground_color},
                          'position': {'x': 30, 'y': 30}, 'size': 30})

        elif not node_dict.get('ids'):
            qbackground_color = '#33D4FF'
            return_category = f"? {node_dict.get('categories', [])[0].split(':')[-1]}"
            nodes.append({'data': {'id': return_category, 'label': return_category},
                          'style': {'background-color': qbackground_color},
                          'position': {'x': 200, 'y': 30}, 'size': 30})

    for edge, edge_data in query_graph["edges"].items():
        predicates = edge_data.get('predicates', [])
        if predicates:
            label = predicates[0].split(':')[-1]
        else:
            label = edge
        edges.append({'data': {'source': return_category, 'target': q_node_ids[0], 'label': label}})
    return nodes + edges


def sifteredges( aux_graph_edges, kg_edges ):
    enrich2group_aux_graph_edge = ''
    group2curie_aux_graph_edge = ''
    for aedge in aux_graph_edges:
        support = [attributes["value"] for attributes in kg_edges[aedge]["attributes"]]
        if support:
            if isinstance(support[0], list):
                enrich2group_aux_graph_edge = aedge
            else:
                group2curie_aux_graph_edge = aedge
    return enrich2group_aux_graph_edge, group2curie_aux_graph_edge


def pickgroup2curieedge(enrichment2group_edge, group2curie_edge, kg_nodes, kg_edges, aux_graphs):
    terminals = [group2curie_edge['subject'], group2curie_edge['object']]
    finaledges = []
    pvalues = set()
    for attributes in enrichment2group_edge["attributes"]:  # ususally one
        enrichment2group_support_graphs = attributes["value"]
        # Each of these exists in the auxiliary graph
        for i, e2group_sp in enumerate(enrichment2group_support_graphs):  # usually 2
            e2group_edges = aux_graphs[e2group_sp]["edges"]
            for e2gedge in e2group_edges:
                edge = kg_edges[e2gedge]
                if edge["subject"] not in terminals and edge["object"] not in terminals:
                    pvalues.add(
                        [att["value"] for att in edge["attributes"] if att['attribute_type_id'] == 'biolink:p_value'][
                            0])

                if edge["subject"] in terminals or edge[
                    "object"] in terminals:  # we are looking for the path  lookupresult--(biolink:member_of)-->uuid:1
                    theedge = [kg_nodes[edge["object"]]["name"], 'has_member', kg_nodes[edge["subject"]]["name"]]
                    subject = edge["subject"]
                    object_ = edge["object"]
                    if subject in terminals:
                        next_element = terminals[
                            terminals.index(subject) + 1] if subject in terminals and terminals.index(
                            subject) + 1 < len(subject) else None
                        finaledge = [kg_nodes[object_]["name"], group2curie_edge["predicate"],
                                     kg_nodes[next_element]["name"]]
                    elif object_ in terminals:
                        next_element = terminals[
                            terminals.index(object_) + 1] if object_ in terminals and terminals.index(
                            object_) + 1 < len(
                            object_) else None
                        finaledge = [group2curie_edge["predicate"], kg_nodes[next_element]["name"]]
                    finaledges.append(theedge + finaledge)
    return pvalues, finaledges


def generate_legend(node_categories, category_colors):
    legend_items = []
    for category in node_categories:
        color = category_colors.get(category, "#000000")  # Default to black if not found
        shape = get_node_shape(node_categories, category)
        legend_items.append(
            html.Div([
                html.Span(
                    style={'display': 'inline-block', 'width': '10px', 'height': '10px', 'background-color': color,
                           'shape': shape}),
                html.Span(f"{category.split(':')[1]} ({shape})", style={'margin-left': '10px', 'font-size': '10px'})
            ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '5px'})
        )

    # Create a responsive flexbox layout with the legend items
    return html.Div(legend_items,
                    style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px', 'align-items': 'right'})


def generate_elements(inference_edge, kg_nodes, kg_edges, aux_graphs, node_categories, category_colors):
    elements_list = []
    support_graphs = [attributes["value"] for attributes in kg_edges[inference_edge]["attributes"] if
                      attributes["attribute_type_id"] == "biolink:support_graphs"]

    enriched2grouplist, lookup_lists, pvalues = generate_rules(inference_edge, kg_nodes, kg_edges, aux_graphs)

    support_graphs_pvalues = sorted(zip(support_graphs, pvalues), key=lambda x: x[1])

    for graph_index, (graph, pvalue) in enumerate(support_graphs_pvalues):
        elements = []
        position_offset = 30  # Offset for each support graph
        position_y = 1 * position_offset
        aux_graph_edges = aux_graphs.get(graph).get("edges")
        for index, auxedge in enumerate(aux_graph_edges):
            kedge = kg_edges[auxedge]
            source = kedge["subject"]
            source_properties = kg_nodes[source]

            if "qualifier" in kedge:
                aspect_qualifier = kedge.get("biolink:object_aspect_qualifier", [])[0] if kedge.get(
                    "biolink:object_aspect_qualifier", []) else ''
                direction_qualifier = kedge.get("biolink:object_direction_qualifier", [])[0] if kedge.get(
                    "biolink:object_direction_qualifier", []) else ''
                predicate = f"{kedge['predicate']} {direction_qualifier} {aspect_qualifier}"
            else:
                predicate = f"{kedge['predicate']}"

            support_graphs2 = [attributes["value"] for attributes in kedge["attributes"] if
                               attributes["attribute_type_id"] == "biolink:support_graphs"]
            if support_graphs2 and isinstance(support_graphs2[0], list):
                predicate = predicate + f"({pvalue})"

            target = kedge["object"]
            target_properties = kg_nodes[target]

            node_size = 10 * len(support_graphs)
            source_color = get_node_color(category_colors, source_properties.get("categories", ["Unknown"])[0])
            target_color = get_node_color(category_colors, target_properties.get("categories", ["Unknown"])[0])
            source_shape = get_node_shape(node_categories, source_properties.get("categories", ["Unknown"])[0])
            target_shape = get_node_shape(node_categories, target_properties.get("categories", ["Unknown"])[0])

            # Positioning nodes to avoid overlap
            position_x = index * position_offset
            sourcedata = {'id': source, 'label': f"{source_properties['name']} ({source})"}
            sourcedata.update(source_properties)
            elements.append({'data': sourcedata,  'position': {'x': position_x, 'y': position_y}, 'style': {'width': node_size, 'height': node_size, 'background-color': source_color, 'shape': source_shape}})
            targetdata = {'id': target, 'label': f"{target_properties['name']} ({target})"}
            targetdata.update(target_properties)
            elements.append({'data': targetdata, 'position': {'x': position_x + 200, 'y': position_y}, 'style': {'background-color': target_color, 'shape': target_shape}})

            predicatedata = {'source': source, 'target': target, 'label': predicate,
                             'support_graphs': support_graphs2}
            elements.append({'data': predicatedata})
            position_y = graph_index * position_offset
        elements_list.append(elements)

    return elements_list, enriched2grouplist, lookup_lists


def generate_rules( selected_inference_edge, kg_nodes, kg_edges, aux_graphs):
    lookup_lists = []
    enriched2grouplist = []
    pvalues = []
    kginference_edge = kg_edges[selected_inference_edge]
    support_graphs = [attributes["value"] for attributes in kginference_edge["attributes"] if
                      attributes["attribute_type_id"] == "biolink:support_graphs"]
    for graph_index, graph in enumerate(support_graphs):  # graph/property
        aux_graph_edges = aux_graphs.get(graph).get("edges")  # usually length 3
        enrich2group_aux_graph_edge, group2curie_aux_graph_edge = sifteredges(aux_graph_edges, kg_edges)

        # 2. enrich2group_aux_graph_edge
        enrichment2group_edge = kg_edges[enrich2group_aux_graph_edge]

        # 3. enrich2group_aux_graph_edge/group2curie_aux_graph_edge
        group2curie_edge = kg_edges[group2curie_aux_graph_edge]
        pvalue, lookupedges = pickgroup2curieedge(enrichment2group_edge, group2curie_edge, kg_nodes, kg_edges, aux_graphs)
        lookup_lists.extend(lookupedges)

        # 2. contd
        pvalue = ', '.join(format(pval, '.4g') for pval in pvalue)
        pvalues.append(pvalue)

        enriched2grouplist.append([kg_nodes[enrichment2group_edge['subject']]['name'], enrichment2group_edge['predicate'], kg_nodes[enrichment2group_edge['object']]['name'], pvalue, ', '.join([source['resource_id'] for source in enrichment2group_edge['sources']])])

    return enriched2grouplist, lookup_lists, pvalues


def onetable(df, tableid):
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in df.columns],
        id=tableid,
        style_table={"overflowY": "auto", "overflowX": "auto", "width": "100%"},
        style_header={'backgroundColor': '#cbd3dd', 'color': 'black', 'fontWeight': 'bold', 'text-align': 'center'},
        style_data_conditional=custom_conditional_style,
        style_cell={'text-align': 'left', "minWidth": "70px", "width": "50px", "maxWidth": "200px",
                    "textOverflow": "ellipsis", 'overflow': 'hidden', 'whiteSpace': 'nowrap'},
        filter_options={"placeholder_text": "Filter column..."},
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        column_selectable="single",
        row_selectable='multi',
        selected_rows=[],
        selected_columns=[],
        page_action='native',
        page_current=0,
        page_size=10,
        fixed_rows={"headers": True, "data": 0},
        fixed_columns={"headers": True, "data": 0},
    )


dbf = pd.DataFrame({})


def vizlayout(answerset):
    if isinstance(answerset, dict):
        try:
            answerset_json = orjson.dumps(answerset).decode('utf-8')
            qg = answerset["message"]["query_graph"]
        except Exception as e:
            logger.error(f"Error in json input in vizlayout function: {type(e).__name__}: {str(e)}")
    if isinstance(answerset, str):
        try:
            qg = orjson.loads(answerset)["message"]["query_graph"]
            answerset_json = answerset
        except Exception as e:
            logger.error(f"Error in string input in vizlayout function: {type(e).__name__}: {str(e)}")

    try:
        layout = dbc.Container([html.Div([
            dcc.Store(id='answerset-input', data=answerset_json),
            dcc.Store(id='stored-node-categories'), dcc.Store(id='stored-category-colors'), dcc.Store(id='stored-kg-nodes'), dcc.Store(id='stored-kg-edges'), dcc.Store(id='stored-aux-graphs'), dcc.Store(id='stored-qg'), dcc.Store(id='stored-results'), dcc.Store(id='stored-inferred-df'),
            dbc.Row([
                dbc.Card(
                    [dbc.CardHeader("Question Graph:", style={"color": "#0096FF", 'background-color': '#cbd3dd'}),
                     dbc.CardBody(cyto.Cytoscape(id='cytoscape-gq',
                                                 style={'width': '80%', 'height': '150px', 'margin': "auto", },
                                                 layout={'name': 'preset', 'directed': True, },
                                                 elements=display_qg(qg),
                                                 stylesheet=[{'selector': 'node', 'style': {'label': 'data(label)'}},
                                                             {'selector': 'edge',
                                                              'style': {'label': 'data(label)', 'curve-style': 'bezier',
                                                                        'target-arrow-shape': 'triangle'}},
                                                             ]
                                                 )
                                  ),
                     ],
                    style={'height': 200}),
            ], style={'margin': '1em'}),
            dbc.Row([
                dbc.Col(html.Div([
                    html.H2("Filter by", style={"color": "#0096FF", 'background-color': '#cbd3dd'}),
                    html.Hr(),
                    html.Center(
                        html.Div(
                            id='inferred-options',
                            children=[
                                dbc.Checklist(
                                    id='inferred-checklist',
                                    options=[
                                        {'label': 'Property', 'value': 'property'},
                                        {'label': 'Graph', 'value': 'graph'},
                                    ],
                                    value=['graph', 'property'],  # Default selections
                                    inline=False
                                )
                            ],
                            style={'padding-left': '20px'}
                            # style={'display': 'none'}  # Initially hidden
                        ),
                    )
                ], style={"padding": "20px", 'background-color': '#cbd3dd', 'height': '65vh'}), width=2),
                dbc.Col(html.Div([html.P("select a row(s) to see the >>inference path", style={'background-color': '#cbd3dd'}), html.Div(id='result-table-container', children=[
                        dash_table.DataTable(
                            id='result-table',
                            columns=[{"name": i, "id": i} for i in dbf.columns],
                            data=dbf.to_dict('records'),
                        )
                    ])]), className="col-10")]),
            dbc.Row([dbc.Col(html.Div(id='cytoscape-cards'), width=8), dbc.Col(html.Div(id='edge-data-table-div'), width=4)]),
            dcc.Store(id='stored-enrichment', data={}),
            dcc.Store(id='stored-lookup', data={}),
            dcc.Store(id='stored-edge-data', data={}),
            ])
        ])
        return layout
    except Exception as e:
        logger.error(f"No message to visualize in vizlayout function: {type(e).__name__}: {str(e)}")


########## Initial Data Storage #############
@callback(Output('stored-qg', 'data'), Output('stored-kg-nodes', 'data'), Output('stored-kg-edges', 'data'), Output('stored-results', 'data'), Output('stored-aux-graphs', 'data'), Output('stored-node-categories', 'data'), Output('stored-category-colors', 'data'), Output('stored-inferred-df', 'data'), Input('answerset-input', 'data'))
def update_stores(json_answerset):
    if not json_answerset:
        return [], [], [], [], [], [], [], []
    answerset = orjson.loads(json_answerset)
    query_graph, kg_edges, kg_nodes, results, aux_graphs = get_answer_components(answerset)
    node_categories = get_all_node_categories(kg_nodes)
    category_colors = generate_color_map(node_categories)

    df = get_inferred_result_df(kg_edges, kg_nodes, results)

    return query_graph, kg_nodes, kg_edges, results, aux_graphs, node_categories, category_colors, df.to_json(orient='split')


########## Display Inference Table #############
@callback([Output('result-table-container', 'children')], [Input('stored-inferred-df', 'data')])
def inferrence(df_json):
    if df_json:
        df = pd.read_json(StringIO(df_json), orient='split')
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            id="result-table",
            style_table={"overflowY": "auto", "overflowX": "auto", "width": "100%"},
            style_header={'backgroundColor': '#cbd3dd', 'color': 'black', 'fontWeight': 'bold', 'text-align': 'center'},
            style_data_conditional=custom_conditional_style,
            style_cell={'text-align': 'left', "minWidth": "70px", "width": "120px", "maxWidth": "200px",
                        "textOverflow": "ellipsis", 'overflow': 'hidden', 'whiteSpace': 'nowrap'},
            filter_options={"placeholder_text": "Filter column..."},
            filter_action="native",
            sort_action="native",
            sort_mode='multi',
            column_selectable="single",
            row_selectable='multi',
            selected_rows=[],
            selected_columns=[],
            page_action='native',
            page_current=0,
            page_size=10,
            fixed_rows={"headers": True, "data": 0},
            fixed_columns={"headers": True, "data": 0},
        ),
    return html.Div(id="result-table", style={'display': 'None'})


########### SideBar Control ######################
@callback(Output('inferred-checklist', 'value'), [Input('inferred-checklist', 'value')])
def update_options(inferred_values):
    if len(inferred_values) != 1:
        return ['graph', 'property']
    return inferred_values


@callback([Output('result-table-container', 'children', allow_duplicate=True)], [Input('inferred-checklist', 'value')], [State('result-table', 'data')], prevent_initial_call=True)
def filter_table( selected_values, data):
    if not selected_values:
        raise PreventUpdate
    else:
        if not data:
            return []
        df = pd.DataFrame(data)
        if len(selected_values) == 2:
            filtered_df = df
        else:
            selected = [', '.join(selected_values)]
            filtered_df = df[df['Enrichment_method'].isin(selected)]
        return dash_table.DataTable(
                data=filtered_df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in filtered_df.columns],
                id="result-table",
                style_table={"overflowY": "auto", "overflowX": "auto", "width": "99%"},
                style_header={'backgroundColor': '#cbd3dd', 'color': 'black', 'fontWeight': 'bold', 'text-align': 'center'},
                style_data_conditional=custom_conditional_style,
                style_cell={'text-align': 'left', "minWidth": "70px", "width": "100px", "maxWidth": "200px",
                            "textOverflow": "ellipsis", 'overflow': 'hidden', 'whiteSpace': 'nowrap'},
                filter_options={"placeholder_text": "Filter column..."},
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                column_selectable="single",
                row_selectable='multi',
                selected_rows=[],
                selected_columns=[],
                page_action='native',
                page_current=0,
                page_size=10,
                fixed_rows={"headers": True, "data": 0},
                fixed_columns={"headers": True, "data": 0},
            ),


# ##### Path Display callbacks ####################
@callback(Output("cytoscape-cards", "children"), Output("stored-lookup", "data"), Output("stored-enrichment", "data"), Input('result-table', "derived_virtual_data"), Input('result-table', "derived_virtual_selected_rows"), Input('stored-kg-nodes', 'data'), Input('stored-kg-edges', 'data'), Input('stored-aux-graphs', 'data'), Input('stored-node-categories', 'data'), Input('stored-category-colors', 'data'), prevent_initial_call=True)
def update_elements( selected_data, selected_rows, kg_nodes, kg_edges, aux_graphs, node_categories, category_colors ):
    if not selected_rows:
        return [], [], []
    selected_results = [selected_data[i]['EdgeString'] for i in selected_rows]

    cards = []
    lookup_basket = {}
    enrichment_basket = {}
    for i, result in enumerate(selected_results):
        elements_list, enriched2grouplist, lookup_lists = generate_elements(result, kg_nodes, kg_edges, aux_graphs, node_categories, category_colors)
        lookup_basket[result] = lookup_lists
        enrichment_basket[result] = enriched2grouplist
        card_body = []
        for j, elements in enumerate(elements_list):
            card_body.append(
                dbc.Row(
                    cyto.Cytoscape(
                        id={'type': 'cytoscape', 'index': f"{i}-{j}"},
                        elements=elements,
                        style={'width': '80%', 'height': '250px', 'margin': "auto", },
                        layout={'name': 'breadthfirst', 'idealEdgeLength': 3, 'nodeRepulsion': 10, 'edgeElasticity': 0.45, 'nestingFactor': 0, 'gravity': 1, 'numIter': 1000},
                        stylesheet=[{'selector': 'node', 'style': {'label': 'data(label)'}},
                                    {'selector': 'edge',
                                     'style': {'label': 'data(label)', 'width': 1, 'curve-style': 'bezier',
                                               'target-arrow-shape': 'triangle'}},
                                    ]

                    ),
                    style={'margin-bottom': '1em'}
                )
            )

        cards.append(
            dbc.Col(
                dbc.Card([dbc.CardHeader(
                    [
                        html.H5(f"{result} has {len(elements_list)} Paths", className="card-title"),
                        generate_legend(node_categories, category_colors),
                        html.Div(html.P("select an edge to view its support graph",
                                        style={'background-color': '#cbd3dd', 'display': 'inline-block'}),
                                 style={'text-align': 'right'}),
                    ]),
                    dbc.CardBody(card_body)],
                    style={'margin-bottom': '1em'}
                )
            )
        )
    return cards, lookup_basket, enrichment_basket


@callback( Output('stored-edge-data', 'data'), Input({'type': 'cytoscape', 'index': ALL}, 'tapEdge'))
def store_edge_data( edge_data ):
    if edge_data and any(edge_data):
        return edge_data[0]['data']
    return {}


@callback(Output('edge-data-table-div', 'children'), Input('stored-edge-data', 'data'), State('stored-lookup', 'data'), State('stored-enrichment', 'data'))
def display_support_graph(edge_data, lookup_basket, enrichment_basket):
    if not edge_data:
        return html.Div()

    support_graphs = edge_data.get('support_graphs', [])

    if not support_graphs:
        return html.Div()

    if support_graphs and isinstance(support_graphs[0], str):
        lookup_baskets = [basket for baskets in lookup_basket.values() for basket in baskets]
        lookup = pd.DataFrame(lookup_baskets, columns=["Object1", "Predicate1", "Subject1", "Predicate2", "Object2"])
        lookup.drop_duplicates(ignore_index=True, inplace=True)

        lookup_table_component = onetable(lookup, 'datatable-lookup-table')
        lookup_table_output = html.Div([html.P("LOOKUP Members ↓ ", style={'backgroundColor': '#cbd3dd'}), lookup_table_component])
        return lookup_table_output
    elif support_graphs and isinstance(support_graphs[0], list):
        enrichment_baskets = [basket for baskets in enrichment_basket.values() for basket in baskets]
        enrichment = pd.DataFrame(enrichment_baskets, columns=["Subject", "Predicate1", "Object", "Pvalue", "Knowledge_Source"])
        enrichment.drop_duplicates(ignore_index=True, inplace=True)
        enrich_table_component = onetable(enrichment, 'datatable-enrich-table')
        enrich_table_output = html.Div([html.P(f"RULE(s) ↓ for the {len(enrichment)} paths", style={'backgroundColor': '#cbd3dd'}), enrich_table_component])
        return enrich_table_output
    return html.Div()