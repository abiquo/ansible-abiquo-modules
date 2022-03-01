#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import traceback
import time
import json
from ansible.module_utils.abiquo import template as template_module
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from abiquo.client import check_response

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: abiquo_template_remove
short_description: Remove existing template from Abiquo cloud platform
description:
    - Remove template from an Abiquo cloud platform
version_added: "2.4"
author: 
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
    token_secret:
        description:
          - OAuth1 token secret
        required: False
        default: null
    datacenter_id:
        description:
          - ID of the datacenter repository where the template should be uploaded
        required: True
    template_id:
        description:
          - Define the id of the template you want to remove
        required: True
    force_remove:
        description:
          - Removes the template even if there is any VM using the template to remove
        required: False
        default: False
'''

EXAMPLES = '''
  - name: Remove template
    abiquo_template_remove:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      abiquo_verify: false
      datacenter_id: 4
      template_id: 54
      enterprise_id: 1
      force_remove: "True"
'''


def core(module):
    enterprise_id = module.params['enterprise_id']
    api_user = module.params['abiquo_api_user']
    api_pass = module.params['abiquo_api_pass']
    datacenter_id = module.params['datacenter_id']
    template_id = module.params['template_id']
    force_remove = module.params['force_remove']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        code, template_removal = remove_template(api, enterprise_id, datacenter_id, template_id, force_remove)
        check_response(204, code, template_removal)
        module.exit_json(
            msg='Template with ID {} removed'.format(template_id),
            code="API response code: {}".format(code),
            changed=True,
        )
    except Exception as ex:
        module.fail_json(msg=ex)


def remove_template(api, enterprise_id, datacenter_id, template_id, force_remove):
    remove_response_code = template_module.remove(api, enterprise_id, datacenter_id, template_id, force_remove)
    return remove_response_code

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        abiquo_api_url=dict(default=None, required=True),
        template_id=dict(default=None, required=True),
        enterprise_id=dict(default=None, required=True),
        datacenter_id=dict(default=None, required=True),
        force_remove=dict(default=False, required=False)
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_template_remove: %s' %
                to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
