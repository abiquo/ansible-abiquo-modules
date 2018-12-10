#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_role_facts
short_description: Gather facts about roles in an Abiquo cloud platform
description:
    - Gather facts about roles in an Abiquo cloud platform
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
    verify:
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
          - Query params for the list roles API call
        required: False
        default: null
    expression:
        description:
          - Expression to apply to the results for further filtering
        required: False
        default: null
'''

EXAMPLES = '''

- name: Gather roles
  abiquo_role_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo

- name: Lookup CLOUD_ADMIN role
  abiquo_role_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    params:
        has: CLOUD_ADMIN

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    params = module.params['params']
    expression = module.params['expression']

    common = AbiquoCommon(module)
    api = common.client

    if params is not None and not "limit" in params:
        params['limit'] = 0

    try:
        c, roles = api.admin.roles.get(
            headers={'Accept': 'application/vnd.abiquo.roles+json'},
            params=params
        )
        common.check_response(200, c, roles)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    if expression is not None:
        r = filter(eval(expression), roles)
        module.exit_json(roles=map(lambda x: x.json, r))
    else:
        module.exit_json(roles=roles.collection)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(default=None, required=True),
            verify=dict(default=True, required=False, type='bool'),
            api_user=dict(default=None, required=False),
            api_pass=dict(default=None, required=False, no_log=True),
            app_key=dict(default=None, required=False),
            app_secret=dict(default=None, required=False),
            token=dict(default=None, required=False, no_log=True),
            token_secret=dict(default=None, required=False, no_log=True),
            params=dict(default=None, required=False, type='dict'),
            expression=dict(default=None, required=False)
        ),
    )

    if module.params['api_user'] is None and module.params['app_key'] is None:
        module.fail_json(msg="either basic auth or OAuth credentials are required")

    if not 'verify' in module.params:
        module.params['verify'] = True

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_role_facts: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
