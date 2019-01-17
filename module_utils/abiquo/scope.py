import json, re

from common import AbiquoCommon
from abiquo.client import check_response

def build_scope_entities(module):
    common = AbiquoCommon(module)
    entities_jsons = module.params.get('scopeEntities')
    
    entities = []

    for entity_json in entities_jsons:
        entity_link = common.getLink(entity_json, 'edit')

        if entity_link is None:
            # An already existing entity
            entities.append(entity_json)
        else:
            entity_type = re.search('abiquo\.(.*)\+', entity_link['type']).group(1)
            json_ent_type = "DATACENTER" if entity_type == "publiccloudregion" else entity_type.upper()

            entity = {
                "idResource": entity_json["id"],
                "type": json_ent_type
            }

            entities.append(entity)

    return entities
