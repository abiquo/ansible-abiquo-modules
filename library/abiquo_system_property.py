#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import traceback
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_system_property
short_description: Manage system properties in an Abiquo cloud platform
description:
    - Manage system properties in an Abiquo cloud platform
    - Allows to add, remove and update system properties from a platform
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
    name:
        description:
          - Name of the system property
        required: True
    value:
        description:
          - Value to set in the system property
        required: True
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Set license in Abiquo
    abiquo_system_property:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      name: some.system.property
      value: super

'''


def core(module):
    name = module.params['name']
    value = module.params['value']
    state = module.params['state']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    c, props = api.config.properties.get(
        headers={'Accept': 'application/vnd.abiquo.systemproperties+json'})
    try:
        common.check_response(200, c, props)
    except Exception as ex:
        module.fail_json(rc=code, msg=ex.message)

    for prop in props:
        if prop.name == name:
            if prop.value == value:
                module.exit_json(
                    msg="Property %s already set" %
                    name, changed=False, prop=prop.json)
            else:
                prop.value = value
                c, prop = prop.put()
                try:
                    common.check_response(200, c, prop)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(
                    msg="Property %s has been updated" %
                    name, changed=True, prop=prop.json)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        value=dict(default=None, required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_system_property: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
