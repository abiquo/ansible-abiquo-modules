import json

from common import AbiquoCommon
from abiquo.client import check_response
import enterprise

def get_for_enterprise_and_type(module, enterprise, htype):
    code, credentials = enterprise.follow('credentials').get()
    check_response(200, code, credentials)

    for cred in credentials:
        if cred._extract_link('hypervisortype')['href'] == htype._extract_link('self')['href']:
            return cred

    return None

def add_for_enterprise_and_type(module, enterprise, htype):
    htype_link = htype._extract_link('self')
    htype_link['rel'] = 'hypervisortype'

    cred_dict = {
        'access': module.params.get('access'),
        'key': module.params.get('key'),
        'links': [ htype_link ]
    }

    code, credential = enterprise.follow('credentials').post(
        headers={
            'accept':'application/vnd.abiquo.publiccloudcredentials+json',
            'content-type':'application/vnd.abiquo.publiccloudcredentials+json',
        },
        data=json.dumps(cred_dict)
    )
    check_response(201, code, credential)

    return credential
