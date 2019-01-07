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

# import module snippets
import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import datacenter
from ansible.module_utils.abiquo import rack

def core(module):
    ip = module.params.get('ip')
    dc_name = module.params.get('datacenter')
    rack_name = module.params.get('rack')
    state = module.params.get('state')

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    
    # dcs = common.get_datacenters()
    dcs = datacenter.list(module)
    dcsf = filter(lambda x: x.name == dc_name, dcs)
    if len(dcs) == 0:
        module.fail_json(rc=1, msg='Datacenter "%s" has not been found!' % dc_name)
    dc = dcsf[0]

    racks = datacenter.get_racks(dc)
    racksf = filter(lambda x: x.name == rack_name, racks)
    if len(racksf) == 0:
        module.fail_json(rc=1, msg='Rack "%s" has not been found!' % rack_name)
    rackdto = racksf[0]

    machines = rack.get_machines(rackdto)
    machine = next((m for m in machines if m.ip == ip), None)
    
    if machine is None:
        # Machine does not exist
        if state == 'absent':
            module.exit_json(msg='Machine with IP %s does not exist' % ip, changed=False)
        else:
            # CREATE IT
            try:
                machine = rack.create_machine(rackdto, module)
                machine_link = machine._extract_link('edit')
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(msg='Machine with IP %s has been created' % ip, changed=True, machine=machine.json, machine_link=machine_link)
    else:
        if state == 'absent':
            try:
                rack.delete_machine(machine)
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(msg='Machine with IP %s has been deleted' % ip, changed=True)
        else:
            machine_link = machine._extract_link('edit')
            module.exit_json(msg='Machine with IP %s already exists' % ip, changed=False, machine=machine.json, machine_link=machine_link)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        ip=dict(default=None, required=True),
        port=dict(default=None, required=True, type=int),
        hyp_type=dict(default=None, required=True),
        ip_service=dict(default=None, required=False),
        user=dict(default='root', required=False),
        password=dict(default='temporal', required=False, no_log=True),
        datastore_name=dict(default=None, required=False),
        datastore_root=dict(default=None, required=False),
        datastore_dir=dict(default=None, required=False),
        service_nic=dict(default=None, required=True),
        datacenter=dict(default=None, required=True),
        rack=dict(default=None, required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    if module.params.get('datastore_name') is None and module.params.get('datastore_root') is None:
        module.fail_json(msg="either datastore_name or datastore_root are required")

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_machine: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
