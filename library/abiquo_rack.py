#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# from __future__ import absolute_import, division, print_function
# __metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_rack
short_description: Manage racks in an Abiquo cloud platform
description:
    - Manage racks in an Abiquo cloud platform private datacenter.
    - Allows to add and remove racks from a datacenter.
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
          - Name of the rack in Abiquo
        required: True
    datacenter:
        description:
          - Name of the datacenter where this rack will be created
        required: True
    vlan_min:
        description:
          - Minimum VLAN tag to use in the rack
        required: False
        default: 2
    vlan_max:
        description:
          - Maximum VLAN tag to use in the rack
        required: False
        default: 4096
    vlan_avoided:
        description:
          - VLAN tags excluded in the range vlan_min - vlan_max
        required: False
        default: null
    vlan_reserved:
        description:
          - How many VLANs are reserved per VDC
        required: False
        default: 1
    nsrq:
        description:
          - Ratio of deployed vs new VLANs in VDCs
        required: False
        default: 10
    ha_enabled:
        description:
          - Whether or not Abiquo HA is enabled for this rack
        required: False
        default: no
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

- name: Create Rack
  abiquo_rack:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: "{{ env_name }}-rack"
    datacenter: "{{ env_name }}-dc"
    vlan_min: 10
    vlan_max: 20

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    name = module.params['name']
    datacenter = module.params['datacenter']
    vlan_min = module.params['vlan_min']
    vlan_max = module.params['vlan_max']
    vlan_avoided = module.params['vlan_avoided']
    vlan_reserved = module.params['vlan_reserved']
    nrsq = module.params['nrsq']
    ha_enabled = eval(module.params['ha_enabled'])
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    datacenters = common.get_datacenters()
    dc = filter(lambda x: x.name == datacenter, datacenters)
    if len(dc) == 0:
        module.fail_json(rc=1, msg='Datcenter "%s" has not been found!' % datacenter)
    dc = dc[0]

    racks = common.get_racks(dc)
    for rack in racks:
        if rack.name == name:
            if state == 'present':
                module.exit_json(msg='Rack "%s" already exists' % name, changed=False, rack=rack.json)
            else:
                c, rresp = rack.delete()
                try:
                    common.check_response(204, c, rresp)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='Rack "%s" deleted' % name, changed=True)

    if state == 'absent':
        module.exit_json(msg='Rack "%s" does not exist' % name, changed=False)
    else:
        rackjson = { 
            'vlanIdMin': vlan_min,
            'vlanIdMax': vlan_max,
            'vlanPerVdcReserved': vlan_reserved,
            'nrsq': nrsq,
            'name': name,
            'vlansIdAvoided': vlan_avoided,
            'haEnabled': ha_enabled
        }

        c, rack = dc.follow('racks').post(
            headers={'accept': 'application/vnd.abiquo.rack+json','content-type': 'application/vnd.abiquo.rack+json'},
            data=json.dumps(rackjson)
        )
        try:
            common.check_response(201, c, rack)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg='Rack "%s" created' % name, changed=True, rack=rack.json)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(default=None, required=True),
            verify=dict(default=True, required=False),
            api_user=dict(default=None, required=False),
            api_pass=dict(default=None, required=False, no_log=True),
            app_key=dict(default=None, required=False),
            app_secret=dict(default=None, required=False),
            token=dict(default=None, required=False, no_log=True),
            token_secret=dict(default=None, required=False, no_log=True),
            name=dict(default=None, required=True),
            datacenter=dict(default=None, required=True),
            vlan_min=dict(default=2, required=False),
            vlan_max=dict(default=4094, required=False),
            vlan_avoided=dict(default=None, required=False),
            vlan_reserved=dict(default=1, required=False),
            nrsq=dict(default=10, required=False),
            ha_enabled=dict(default=False, required=False),
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
        module.fail_json(msg='Unanticipated error running abiquo_rack: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
