import json

from ansible.module_utils.abiquo.common import AbiquoCommon
from abiquo.client import check_response


def list(module):
    common = AbiquoCommon(module)
    api = common.client

    code, datacenters = api.admin.datacenters.get(
        headers={'Accept': 'application/vnd.abiquo.datacenters+json'})
    check_response(200, code, datacenters)

    all_dcs = []
    for dc in datacenters:
        all_dcs.append(dc)

    return all_dcs


def get_network_service_types(dc):
    c, stypes = dc.follow('networkservicetypes').get()
    check_response(200, c, stypes)

    all_types = []
    for stype in stypes:
        all_types.append(stype)

    return all_types


def get_racks(datacenter):
    code, racks = datacenter.follow('racks').get()
    check_response(200, code, racks)

    all_racks = []
    for rack in racks:
        all_racks.append(rack)

    return all_racks


def delete_rack(rack):
    code, resp = rack.delete()
    check_response(204, code, resp)


def create_rack(datacenter, module):
    name = module.params.get('name')
    vlan_min = module.params.get('vlan_min')
    vlan_max = module.params.get('vlan_max')
    vlan_avoided = module.params.get('vlan_avoided')
    vlan_reserved = module.params.get('vlan_reserved')
    nrsq = module.params.get('nrsq')
    ha_enabled = module.params.get('ha_enabled')

    rackjson = {
        'vlanIdMin': vlan_min,
        'vlanIdMax': vlan_max,
        'vlanPerVdcReserved': vlan_reserved,
        'nrsq': nrsq,
        'name': name,
        'vlansIdAvoided': vlan_avoided,
        'haEnabled': ha_enabled
    }

    code, rack = datacenter.follow('racks').post(
        headers={'accept': 'application/vnd.abiquo.rack+json',
                 'content-type': 'application/vnd.abiquo.rack+json'},
        data=json.dumps(rackjson)
    )
    check_response(201, code, rack)

    return rack


def discover(dc, disc_query_params):
    c, hypdisc = dc.follow('discover').get(params=disc_query_params)
    check_response(200, c, hypdisc)
    return hypdisc.collection[0]


def get_datacenter_repo(datacenter, module):
    common = AbiquoCommon(module)
    common.login()

    code, enterprise = common.user.follow('enterprise').get()
    check_response(200, code, enterprise)

    code, repos = enterprise.follow('datacenterrepositories').get()
    check_response(200, code, repos)

    filtered_repos = filter(lambda x: x._has_link('datacenter')
                            and x._extract_link('datacenter')['title'] == datacenter, repos)
    if len(filtered_repos) == 0:
        return None
    return filtered_repos[0]


def find_template(module):
    template_name = module.params.get('template_name')
    datacenter = module.params.get('datacenter')

    repo = get_datacenter_repo(datacenter, module)
    if repo is None:
        raise Exception("Datacenter repo for datacenter %s not found!" % datacenter)

    code, templates = repo.follow('virtualmachinetemplates').get()
    check_response(200, code, templates)

    template = filter(lambda x: x.name == template_name, templates)
    if len(template) == 0:
        return None
    else:
        return template[0]
