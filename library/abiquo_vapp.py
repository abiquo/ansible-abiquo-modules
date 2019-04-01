#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_vapp
short_description: Manage virtual appliances in an Abiquo cloud platform
description:
    - Manage virtual appliances in an Abiquo cloud platform
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
          - The VDC where to create the vApp.
        required: True
    name:
        description:
          -  Name of the virtual appliance.
        required: True
    iconUrl:
        description:
          -  URL of the virtual appliance icon
        required: False
    description:
        description:
          -  Description of the virtual appliance
        required: False
    force:
        description:
          - Wether or not to force the operation.
        required: False
    restricted:
        description:
          - Define if the vapp is an restricted vapp.
        required: False
    state:
        description:
          - State of the vApp
        required: True
        choices: ["present", "absent", "undeploy", "deploy"]
        default: "present"
'''

EXAMPLES = '''

- name: Create vApp 'vapp1'
  abiquo_vdc:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: vapp1
    vdc: "{{ vdc }}"

- name: Create vApp 'vdc2'
  abiquo_vdc:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: vapp1
    iconUrl: http://somefancy.icon/icon.png
    vdc: "{{ vdc }}"

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import vapp as virtualappliance

def lookup_vapp(module):
    vdc_link = module.params.get('vdc')
    vapp_name = module.params.get('name')

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)

    vapp = None
    try:
        vdc = common.get_dto_from_link(vdc_link)
        vapp = virtualappliance.find_vapp_in_vdc(vdc, vapp_name)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    return vapp

def vapp_present(module):
    vapp = lookup_vapp(module)

    if vapp is None:
        try:
            vapp = virtualappliance.create_vapp(module)
        except ValueError as exv:
            module.fail_json(msg=exv.message)
        except Exception as ex:
            module.fail_json(msg=ex.message)

        vapp_link = vapp._extract_link('edit')
        module.exit_json(msg='vApp "%s" created' % vapp.name, changed=True, vapp=vapp.json, vapp_link=vapp_link)
    else:
        vapp_link = vapp._extract_link('edit')
        module.exit_json(msg='vApp "%s" already exists' % vapp.name, changed=False, vapp=vapp.json, vapp_link=vapp_link)

def vapp_absent(module):
    vapp = lookup_vapp(module)

    if vapp is None:
        module.exit_json(msg='vApp "%s" does not exist' % module.params.get('name'), changed=False)
    else:
        try:
            virtualappliance.delete_vapp(vapp, module)
        except Exception as ex:
            module.fail_json(msg=ex.message)
        module.exit_json(msg='vApp "%s" deleted' % vapp.name, changed=True)

def vapp_deploy(module):
    vapp = lookup_vapp(module)

    if vapp is None:
        module.exit_json(msg='vApp "%s" does not exist' % module.params.get('name'), changed=False)
    else:
        vapp_link = vapp._extract_link('edit')

        if vapp.state == 'DEPLOYED':
            module.exit_json(msg='vApp "%s" is already deployed' % vapp.name, changed=False, vapp=vapp.json, vapp_link=vapp_link)
        else:
            try:
                vapp = virtualappliance.deploy_vapp(vapp, module)
                if state != 'DEPLOYED':
                    module.fail_json(msg='vApp "%s" is not in the desired state', vapp=vapp.json, vapp_link=vapp_link)
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(msg='vApp "%s" has been deployed' % vapp.name, changed=True, vapp=vapp.json, vapp_link=vapp_link)

def vapp_undeploy(module):
    vapp = lookup_vapp(module)

    if vapp is None:
        module.exit_json(msg='vApp "%s" does not exist' % module.params.get('name'), changed=False)
    else:
        vapp_link = vapp._extract_link('edit')

        if vapp.state in [ 'NOT_ALLOCATED', 'NOT_DEPLOYED' ]:
            module.exit_json(msg='vApp "%s" is already undeployed' % vapp.name, changed=False, vapp=vapp.json, vapp_link=vapp_link)
        else:
            try:
                vapp = virtualappliance.undeploy_vapp(vapp, module)
                if state not in [ 'NOT_ALLOCATED', 'NOT_DEPLOYED' ]:
                    module.fail_json(msg='vApp "%s" is not in the desired state', vapp=vapp.json, vapp_link=vapp_link)
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(msg='vApp "%s" has been undeployed' % vapp.name, changed=True, vapp=vapp.json, vapp_link=vapp_link)

def core(module):
    state = module.params.get('state')

    if state == 'present':
        vapp_present(module)
    elif state == 'absent':
        vapp_absent(module)
    elif state == 'deploy':
        vapp_deploy(module)
    elif state == 'undeploy':
        vapp_undeploy(module)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        vdc=dict(default=None, required=True, type='dict'),
        iconUrl=dict(default=None, required=False),
        description=dict(default=None, required=False),
        restricted=dict(default=False, required=False, type='bool'),
        force=dict(default=False, required=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent', 'undeploy', 'deploy']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_vapp: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
