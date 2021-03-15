#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo import public_cloud_credentials as credential_module
from ansible.module_utils.abiquo import hypervisortype as htype_module
from ansible.module_utils.abiquo import enterprise as enterprise_module
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_public_cloud_credentials
short_description: Manage enterprises' public cloud credentials in an Abiquo cloud platform
description:
    - Manage enterprises' public cloud credentials in an Abiquo cloud platform
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

    key:
        description:
          - Key for the credentials
        required: True
    access:
        description:
          - Access identifier of the credentials
        required: True

    enterprise:
        description:
          - An enterprise link to the enterprise where to add the credentials as returned by abiquo_enterprise_facts module (or an equivalent dict)
        required: True
    hypervisortype:
        description:
          - An hypervisortype link for which the credentials are valid as returned by abiquo_hypervisortype_facts module (or an equivalent dict)
        required: True

    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create an enterprise
  abiquo_enterprise:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: some_enterprise
  register: abiquoEnterprise

- name: Add credentials
  abiquo_public_cloud_credentials:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    access: some_aws_access_key
    key: some_aws_secret_key
    enterprise: "{{ abiquoEnterprise.enterprise_link }}"
    hypervisortype: "{{ htype.hypervisortype_link }}"

'''


def lookup_enterprise_htype(module):
    enterprise_link = module.params.get('enterprise')
    htype_link = module.params.get('hypervisortype')
    enterprise = enterprise_module.find_by_link(module, enterprise_link)
    htype = htype_module.find_by_link(module, htype_link)

    if enterprise is None:
        module.fail_json(
            msg='Could not find enterprise identified by link "%s"' %
            json.dumps(enterprise_link))

    return enterprise, htype


def pcr_creds_present(module):
    enterprise, htype = lookup_enterprise_htype(module)

    credential = None
    try:
        credential = credential_module.get_for_enterprise_and_type(
            module, enterprise, htype)
    except Exception as e:
        module.fail_json(msg=e.message)

    if credential is not None:
        module.exit_json(msg='Enterprise \'%s\' already has *some* credentials for %s' % (enterprise.name, htype.realName),
                         changed=False, credential=credential.json, credential_link=credential._extract_link('edit'))
    else:
        try:
            credential = credential_module.add_for_enterprise_and_type(
                module, enterprise, htype)
        except Exception as e:
            module.fail_json(msg=e.message)

        module.exit_json(msg='Credentials added to enterprise \'%s\' for provider %s' % (enterprise.name, htype.realName),
                         changed=True, credential=credential.json, credential_link=credential._extract_link('edit'))


def pcr_creds_absent(module):
    enterprise, htype = lookup_enterprise_htype(module)

    credential = credential_module.get_for_enterprise_and_type(
        module, enterprise, htype)
    if credential is None:
        module.exit_json(msg='Enterprise \'%s\' has no credentials for %s' % (enterprise.name, htype.realName),
                         changed=False)
    else:
        try:
            credential.delete()
        except Exception as e:
            module.fail_json(msg=e.message)

        module.exit_json(msg='Credentials deleted for provider %s in enterprise \'%s\' ' % (htype.realName, enterprise.name),
                         changed=True)


def core(module):
    state = module.params.get('state')

    if state == 'present':
        pcr_creds_present(module)
    else:
        pcr_creds_absent(module)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        access=dict(default=None, required=True, type='str'),
        key=dict(default=None, required=True, type='str'),
        enterprise=dict(default=None, required=True, type='dict'),
        hypervisortype=dict(default=None, required=True, type='dict'),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_public_cloud_credentials: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
