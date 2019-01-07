#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_datacenter
short_description: Manage datacenters in an Abiquo cloud platform
description:
    - Manage datacenters in an Abiquo cloud platform
    - Allows to add and remove datacenters from a platform
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
          - Name of the datacenter in Abiquo
        required: True
    location:
        description:
          - Location of the datacenter
        required: True
    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create datacenter 'dc1'
  abiquo_datacenter:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: dc1
    location: Somewhere over the rainbows

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec

def core(module):
    name = module.params['name']
    location = module.params['location']
    state = module.params['state']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        c, datacenters = api.admin.datacenters.get(headers={'Accept': 'application/vnd.abiquo.datacenters+json'})
        common.check_response(200, c, datacenters)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for dc in datacenters:
        if dc.name == name:
            if state == 'present':
                module.exit_json(msg='Datacenter "%s"' % name, changed=False, dc=dc.json)
            else:
                c, dcresp = dc.delete()
                try:
                    common.check_response(204, c, dcresp)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='Datacenter "%s" deleted' % name, changed=True)

    if state == 'absent':
        module.exit_json(msg='Datacenter "%s"' % name, changed=False)
    else:
        dc = { "name": name, "location": location }
        c, datacenter = api.admin.datacenters.post(
            headers={'Accept': 'application/vnd.abiquo.datacenter+json','Content-Type': 'application/vnd.abiquo.datacenter+json'},
            data=json.dumps(dc)
        )
        try:
            common.check_response(201, c, datacenter)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg='Datacenter "%s" created' % name, changed=True, dc=datacenter.json)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        location=dict(default=None, required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_datacenter: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
