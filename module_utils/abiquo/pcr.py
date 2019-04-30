import json

from common import AbiquoCommon
from abiquo.client import check_response

def list(module):
    common = AbiquoCommon(module)
    api = common.client

    code, pcrs = api.admin.publiccloudregions.get(headers={'Accept': 'application/vnd.abiquo.publiccloudregions+json'})
    check_response(200, code, pcrs)

    all_pcrs = []
    for pcr in pcrs:
        all_pcrs.append(pcr)

    return all_pcrs

def find_by_link(module, pcr_link):
    common = AbiquoCommon(module)
    api = common.client

    code, publiccloudregions = api.admin.publiccloudregions.get(headers={'accept': 'application/vnd.abiquo.publiccloudregions+json'},
        params={'has': pcr_link['title']})
    check_response(200, code, publiccloudregions)

    for pcr in publiccloudregions:
        public_cloud_region_link = filter(lambda x: x['rel'] == 'edit', pcr.links)[0]
        if public_cloud_region_link['href'] == pcr_link['href']:
            return pcr

    return None

def lookup_region(module):
    common = AbiquoCommon(module)
    provider = module.params.get('provider')
    region = module.params.get('region')

    c, htypes = common.client.config.hypervisortypes.get(headers={'accept':'application/vnd.abiquo.hypervisortypes+json'})
    check_response(200, c, htypes)

    htype = filter(lambda x: x.name == provider, htypes)
    if len(htype) == 0:
        return None
    htype = htype[0]

    c, regions = htype.follow('regions').get()
    check_response(200, c, regions)

    region = filter(lambda x: x.name == region, regions)    
    if len(region) == 0:
        return None
    region = region[0]

    return region

def create_pcr(region, module):
    common = AbiquoCommon(module)

    reglnk = region._extract_link('self')
    reglnk['rel'] = 'region'
    pcrjson = {
        'name': module.params.get('name'),
        'provider': module.params.get('provider'),
        'links': [ reglnk ]
    }
    c, pcr = common.client.admin.publiccloudregions.post(
        headers={'accept': 'application/vnd.abiquo.publiccloudregion+json',
                'content-Type': 'application/vnd.abiquo.publiccloudregion+json'},
        data=json.dumps(pcrjson)
    )
    common.check_response(201, c, pcr)

    return pcr

def hypervisortype(location):
    htype_link = location._extract_link('hypervisortype')
    return htype_link
