#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_datacenter_facts
short_description: Gather facts about datacenters in an Abiquo cloud platform
description:
    - Gather facts about datacenters in an Abiquo cloud platform
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
    params:
        description:
          - Query params for the list datacenters API call
        required: False
        default: null
    expression:
        description:
          - Expression to apply to the results for further filtering
        required: False
        default: null
'''

EXAMPLES = '''

- name: Lookup datacenters
  abiquo_datacenter_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    params:
        has: "Somename"

- name: Lookup datacenters with Hyper-V hypervisors
  abiquo_datacenter_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    expression: "HYPERV_301 in map(lambda x: x._extract_link('hypervisortype')['title'] , datacenters)"

'''


def core(module):
    params = module.params['params']
    expression = module.params['expression']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        c, datacenters = api.admin.datacenters.get(
            headers={'Accept': 'application/vnd.abiquo.datacenters+json'},
            params=params
        )
        common.check_response(200, c, datacenters)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    if expression is not None:
        dcs = filter(eval(expression), datacenters)
        module.exit_json(dcs=map(lambda x: x.json, dcs))
    else:
        module.exit_json(dcs=datacenters.collection)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        params=dict(default=None, required=False, type='dict'),
        expression=dict(default=None, required=False)
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_datacenter_facts: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
