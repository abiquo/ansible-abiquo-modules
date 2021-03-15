import json

from common import AbiquoCommon
from abiquo.client import check_response


def list(module):
    common = AbiquoCommon(module)
    api = common.client

    all_htypes = []

    code, htypes = api.config.hypervisortypes.get(
        headers={'Accept': 'application/vnd.abiquo.hypervisortypes+json'})
    common.check_response(200, code, htypes)

    for htype in htypes:
        all_htypes.append(htype)

    return all_htypes


def find_by_link(module, link):
    hypervisortypes = list(module)

    for htype in hypervisortypes:
        htype_link = filter(lambda x: x['rel'] == 'self', htype.links)[0]
        if htype_link['href'] == link['href']:
            return htype

    return None
