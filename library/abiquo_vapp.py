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
    restricted:
        description:
          - Define if the vapp is an restricted vapp.
        required: False
    state:
        description:
          - State of the vApp
        required: True
        choices: ["present", "absent"]
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

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    name = module.params['name']
    vdc_json = module.params['vdc']
    iconUrl = module.params['iconUrl']
    description = module.params['description']
    restricted = module.params['restricted']
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    vdc = common.getDTO(vdc_json)
    if vdc is None:
        module.fail_json(rc=c, msg="VDC '%s' not found!" % vdc_json['name'])

    try:
        code, vapps = vdc.follow('virtualappliances').get()
        common.check_response(200, code, vapps)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for vapp in vapps:
        if vapp.name == name:
            if state == 'present':
                module.exit_json(msg='vApp "%s"' % name, changed=False, vapp=vapp.json, vapp_link=vapp._extract_link('edit'))
            else:
                c, response = vapp.delete()
                try:
                    common.check_response(204, c, response)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='vApp "%s" deleted' % name, changed=True)

    if state == 'absent':
        module.exit_json(msg='vApp "%s"' % name, changed=False)
    else:
        vapp_dict = {
            "name": name,
            "iconUrl": iconUrl,
            "description": description,
            "restricted": restricted
        }

        c, vapp = vdc.follow('virtualappliances').post(
            headers={'accept': 'application/vnd.abiquo.virtualappliance+json',
                    'content-Type': 'application/vnd.abiquo.virtualappliance+json'},
            data=json.dumps(vapp_dict)
        )
        try:
            common.check_response(201, c, vapp)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg='vApp "%s" created' % name, changed=True, vapp=vapp.json, vapp_link=vapp._extract_link('edit'))

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
            name=dict(default=None, required=True),
            vdc=dict(default=None, required=True, type='dict'),
            iconUrl=dict(default=None, required=False),
            description=dict(default=None, required=False),
            restricted=dict(default=False, required=False, type='bool'),
            state=dict(default='present', choices=['present', 'absent']),
        ),
    )

    if module.params['api_user'] is None and module.params['app_key'] is None:
        module.fail_json(msg="either basic auth or OAuth credentials are required")

    if not 'verify' in module.params:
        module.params['verify'] = True

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_vapp: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
