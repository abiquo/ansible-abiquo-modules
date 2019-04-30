import json, re

from common import AbiquoCommon
from common import abiquo_updatable_arguments
from abiquo.client import check_response

def lookup_by_name(module):
    common = AbiquoCommon(module)
    api = common.client

    code, scopes = api.admin.scopes.get(headers={'accept':'application/vnd.abiquo.scopes+json'})
    common.check_response(200, code, scopes)

    for scope in scopes:
        if scope.name == module.params.get('name'):
            return scope

    return None

def update(module, scope):
    common = AbiquoCommon(module)

    for k, v in abiquo_updatable_arguments(module.argument_spec):
        if v is not None:
            scope.json[k] = v

    scope.json["scopeEntities"] = build_scope_entities(module)

    parent = module.params.get('scopeParent')
    if parent is not None:
        parent_link = common.getLink(parent, 'edit')
        parent_link['rel'] = 'scopeParent'
        scope.json['links'] = [ parent_link ]

    code, scope = scope.follow('edit').put(
        headers={'accept':'application/vnd.abiquo.scope+json','content-type':'application/vnd.abiquo.scope+json'},
        data=json.dumps(scope.json)
    )
    common.check_response(200, code, scope)
    return scope

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

def create(module):
    common = AbiquoCommon(module)
    api = common.client

    scope_json = {
        "name": module.params.get('name'),
        "automaticAddDatacenter": module.params.get('automaticAddDatacenter'),
        "automaticAddEnterprise": module.params.get('automaticAddEnterprise')
    }
    scope_json["scopeEntities"] = build_scope_entities(module)

    if module.params.get('scopeParent') is not None:
        parent_link = common.getLink(module.params['scopeParent'], 'edit')
        parent_link['rel'] = 'scopeParent'
        scope_json['links'] = [ parent_link ]

    code, scope = api.admin.scopes.post(
        headers={'accept':'application/vnd.abiquo.scope+json','content-type':'application/vnd.abiquo.scope+json'},
        data=json.dumps(scope_json)
    )
    common.check_response(201, c, scope)

    return scope
