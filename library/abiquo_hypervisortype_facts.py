#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo import hypervisortype as htype_module
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_hypervisortype_facts
short_description: Gather facts on Abiquo available hypervisor types
description:
    - Allows to gather info about the available hypervisor types in an Abiquo cloud.
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
    expression:
        description:
          - Expression to apply to the results for further filtering
        required: False
        default: null
'''

EXAMPLES = '''

- name: Gather all available hypervisor types
  abiquo_hypervisortype_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
  register: htypes

- name: Lookup hypervisor type "some_provider"
  abiquo_hypervisortype_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    expression: "name == 'some_provider'"
  register: htypes

'''

RETURN = '''
hypervisortypes:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        baseformat:
            description: Base format of the hypervisor type
            returned: always
            type: String
        compatibilityTable:
            description: Template format compatibility table
            returned: always
            type: Collection of String
        diskControllerTypes:
            description: List of compatible disk controllers
            returned: always
            type: Collection of String
        diskAllocationTypes:
            description: List of compatible disk allocation types
            returned: always
            type: Collection of String
        ethernetDrivers:
            description: List of compatible ethernet drivers
            returned: always
            type: Collection of String
        name:
            description: Name of the hypervisor type
            returned: always
            type: String
        realName:
            description: Friendly name of the hypervisor type
            returned: always
            type: String
        constraints:
            description: Hypervisor plugin constraints
            returned: always
            type: Collection of String
        guestSetups:
            description: List of compatible guest setups
            returned: always
            type: Collection of String
        operations:
            description: Hypervisor operations
            returned: always
            type: Collection of String
        links:
            description: The collection of dicts representing links to related objects.
            returned: always
            type: list
'''


def core(module):
    expression = module.params.get('expression')

    try:
        hypervisor_types = htype_module.list(module)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for htype in hypervisor_types:
        htype.__setattr__('hypervisortype_link', htype._extract_link('self'))

    if expression is not None:
        htypes = filter(eval(expression), hypervisor_types)
        module.exit_json(hypervisortypes=map(lambda x: x.json, htypes))
    else:
        module.exit_json(hypervisortypes=hypervisor_types)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        expression=dict(default=None, required=False)
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_hypervisortype_facts: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
