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
module: abiquo_vdc_template_facts
short_description: Gather facts on Abiquo templates available in a given Virtual datacenter
description:
    - Gather facts on Abiquo templates available in a given Virtual datacenter
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
    vdc:
        description:
          - The VDC where to lookup templates
        required: True
    params:
        description:
          - A collection of params to filter the search
        required: False
'''

EXAMPLES = '''

- name: Gather available templates in VDC 'someVDC'
  abiquo_vdc_template_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    vdc: "{{ vdc }}"

- name: Gather available templates in VDC 'someVDC' with 'test' in the name
  abiquo_vdc_template_facts:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    vdc: "{{ vdc }}"
    params:
        has: test
'''

RETURN = '''
templates:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains: Check Abiquo API documentation
'''


def core(module):
    vdc_json = module.params['vdc']
    params = module.params['params']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    vdc = common.getDTO(vdc_json)
    if vdc is None:
        module.fail_json(rc=c, msg="VDC '%s' not found!" % vdc_json['name'])

    code, templates = vdc.follow('templates').get(params=params)
    try:
        common.check_response(200, code, templates)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    all_templates = []
    for template in templates:
        j = template.json
        j['template_link'] = template._extract_link('edit')
        all_templates.append(j)

    module.exit_json(templates=all_templates)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        vdc=dict(default=None, required=True, type='dict'),
        params=dict(default={}, required=False, type='dict'),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_vdc_template_facts: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
