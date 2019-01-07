#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_location_facts
short_description: Gather facts on Abiquo available locations
description:
    - Allows to gather info about the available locations in an Abiquo cloud.
version_added: "2.4"
author: "Marc Cirauqui (@chirauki)"
requirements:
    - "python >= 2.6"
    - "abiquo-api >= 0.1.13"
options:
    api_url:
        description:
          - Define the Abiquo API endpoint URL
        required: True
    ssl_verify:
        description:
          - Whether or not to verify SSL certificates.
        required: False
        default: True
    api_user:
        description:
          - API username
        required: False
        default: null
    api_pass:
        description:
          - API password
        required: False
        default: null
    app_key:
        description:
          - OAuth1 application key
        required: False
        default: null
    app_secret:
        description:
          - OAuth1 application secret
        required: False
        default: null
    token:
        description:
          - OAuth1 token
        required: False
        default: null
    token_secret:
        description:
          - OAuth1 token secret
        required: False
        default: null
    enterprise:
        description:
          - Query locations for this enterprise (id)
        required: False
    has:
        description:
          - If present filter to apply in the search.
        required: False
    inscope:
        description:
          - The private network to create in the VDC.
        required: False
'''

EXAMPLES = '''

- name: Gather available locations having 'someLocation'
  abiquo_location_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    has: someLocation

- name: Gather all available locations
  abiquo_location_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo

'''

RETURN = '''
locations:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        id:
            description: The ID of the location.
            returned: always
            type: string
        name:
            description: The name of the location.
            returned: always
            type: string
        links:
            description: The collection of dicts representing links to related objects.
            returned: always
            type: list
'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec

def core(module):
    enterprise = module.params['enterprise']
    has = module.params['has']
    inscope = module.params['inscope']
    
    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    locations = []
    params = {}
    if has is not None:
        params['has'] = has
    if enterprise is not None:
        params['enterprise'] = enterprise
    if inscope is not None:
        params['inscope'] = inscope

    c, datacenters = api.cloud.locations.get(headers={'Accept': 'application/vnd.abiquo.datacenters+json'},
                                             params=params)
    try:
        common.check_response(200, c, datacenters)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for dc in datacenters:
        locations.append(dc.json)

    c, pcrs = api.cloud.locations.get(headers={'Accept': 'application/vnd.abiquo.publiccloudregions+json'},
                                             params=params)
    try:
        common.check_response(200, c, pcrs)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for pcr in pcrs:
        locations.append(pcr.json)

    module.exit_json(locations=locations)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        enterprise=dict(default=None, required=False),
        has=dict(default=None, required=False),
        inscope=dict(default=None, required=False),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_location_facts: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
