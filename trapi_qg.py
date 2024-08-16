import json
from string import Template

def qg_template():
    return '''{
        "query_graph": {
            "nodes": {
                "drug": {
                    "ids": $source_id,
                    "constraints": [],
                    "is_set": false,
                    "categories":  $source_category
                },
                "disease": {
                    "ids": $target_id,
                    "is_set": false,
                    "constraints": [],
                    "categories": $target_category
                }
            },
            "edges": {
                "e00": {
                    "subject": "drug",
                    "object": "disease",
                    "predicates": $predicate,
                    "knowledge_type": "inferred",
                    "attribute_constraints": [],
                    "qualifier_constraints": $qualifier
                }
            }
        }
    }'''


def get_qg( curie, is_source, predicates, source_category='', target_category='', object_aspect_qualifier=None,
            object_direction_qualifier=None ):
    # print('curie= ', curie, '\nis_source = ', is_source, '\npredicates = ', predicates, '\nsource_category = ',
    #       source_category, '\ntarget_category = ', target_category)

    if not is_source:
        target_ids = curie
        source_ids = []
    else:
        source_ids = curie
        target_ids = []

    source_category = [source_category] if source_category else []
    target_category = [target_category] if target_category else []

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

    query_template = Template(qg_template())
    qs = query_template.substitute(source_id=json.dumps(source_ids), target_id=json.dumps(target_ids),
                                   source_category=json.dumps(source_category),
                                   target_category=json.dumps(target_category),
                                   predicate=json.dumps(predicates), qualifier=json.dumps(quali))

    query = json.loads(qs)
    if not is_source:
        del query["query_graph"]["nodes"]["drug"]["ids"]
        query["query_graph"]["nodes"]["disease"]["ids"] = target_ids
    else:
        del query["query_graph"]["nodes"]["disease"]["ids"]
        query["query_graph"]["nodes"]["drug"]["ids"] = source_ids

    return {"message": query}