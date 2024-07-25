import json
from string import Template

def qg_template():
    return '''{
        "query_graph": {
            "nodes": {
                "$source": {
                    "ids": $source_id,
                    "constraints": [],
                    "is_set": false,
                    "categories":  $source_category
                },
                "$target": {
                    "ids": $target_id,
                    "is_set": false,
                    "constraints": [],
                    "categories": $target_category
                    }
            },
            "edges": {
                "e00": {
                    "subject": "$source",
                    "object": "$target",
                    "predicates": $predicate,
                    "knowledge_type": "inferred",
                    "attribute_constraints": [],
                    "qualifier_constraints": $qualifier

                }
            }
        }
    }
'''

def get_qg(curie, is_source, predicates, source_category = '', target_category='',  object_aspect_qualifier=None, object_direction_qualifier=None):
    if not is_source:
        target_ids = curie
        source_ids = []
    else:
        source_ids = curie
        target_ids = []


    source = source_category.split(":")[1].lower() if source_category else 'n0'
    target = target_category.split(":")[1].lower() if target_category else 'n1'
    query_template = Template(qg_template())
    query = {}

    source_category = [source_category] if source_category else []
    target_category = [target_category] if target_category else []
    # source_ids = source_ids if source_ids != None else []

    # is_source = True if source_ids else False

    quali = []
    if object_aspect_qualifier and object_direction_qualifier:
        quali = [
            {
                "qualifier_set": [
                    {
                        "qualifier_type_id": "biolink:object_aspect_qualifier",
                        "qualifier_value": object_aspect_qualifier
                    },
                    {
                        "qualifier_type_id": "biolink:object_direction_qualifier",
                        "qualifier_value": object_direction_qualifier
                    }
                ]
            }
        ]


    qs = query_template.substitute(source=source, target=target, source_id=json.dumps(source_ids),
                                   target_id=json.dumps(target_ids),
                                   source_category=json.dumps(source_category),
                                   target_category=json.dumps(target_category), predicate=json.dumps(predicates),
                                   qualifier=json.dumps(quali))

    try:
        query = json.loads(qs)
        if not is_source:
            del query["query_graph"]["nodes"][source]["ids"]
            # query["query_graph"]["nodes"][target]["is_set"] = True
        else:
            del query["query_graph"]["nodes"][target]["ids"]
            # query["query_graph"]["nodes"][source]["is_set"] = True
    except UnicodeDecodeError as e:
        print(e)
    # print('query: ', query)
    return query