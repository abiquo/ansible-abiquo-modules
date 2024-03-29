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
module: abiquo_enterprise_properties
short_description: Manage enterprise properties in an Abiquo cloud platform
description:
    - Manage enterprise properties in an Abiquo cloud platform
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
    properties:
        description:
          - Properties set for this enterprise
        required: True
    enterprise:
        description:
          - Enterprise where to add the properties as returned by abiquo_enterprise module (or an equivalent dict)
        required: True
'''

EXAMPLES = '''

- name: Create an enterprise
  abiquo_enterprise:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: an
    workflow: yes
  register: an_enterprise

- name: Set properties for an enterprise
  abiquo_enterprise_properties:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    properties:
      foo: bar
      bar: baz
    enterprise: "{{ an_enterprise.enterprise }}"

'''


def core(module):
    properties = module.params['properties']
    enterprise = module.params['enterprise']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client
    props = None
    ent = None

    try:
        c, ent = api.admin.enterprises.get(
            id="%s" %
            enterprise['id'], headers={
                'accept': 'application/vnd.abiquo.enterprise+json'})
        common.check_response(200, c, ent)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    try:
        c, props = ent.follow('properties').get()
        common.check_response(200, c, props)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    cloned_props = props.properties.copy()
    cloned_props.update(properties)

    properties_json = {
        'properties': cloned_props
    }

    c, props = ent.follow('properties').put(
        headers={
            'accept': 'application/vnd.abiquo.enterpriseproperties+json',
            'content-type': 'application/vnd.abiquo.enterpriseproperties+json'
        },
        data=json.dumps(properties_json)
    )

    try:
        common.check_response(200, c, props)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)
    module.exit_json(changed=True, properties=props.json)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        properties=dict(default=None, required=True, type='dict'),
        enterprise=dict(default=None, required=True, type='dict'),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_enterprise_properties: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
