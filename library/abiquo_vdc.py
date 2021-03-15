#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo import pcr as pcr_module
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_vdc
short_description: Manage virtual datacenters in an Abiquo cloud platform
description:
    - Manage virtual datacenters in an Abiquo cloud platform
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
          - Name of the virtual datacenter in Abiquo
        required: True
    enterprise:
        description:
          - Enterprise where to create the VDC as returned by abiquo_enterprise_facts module (or an equivalent dict)
        required: True
    location:
        description:
          - Location for the virtual datacenter as returned by abiquo_location_facts module (or an equivalent dict)
        required: True
    hypervisortype:
        description:
          - Hypervisor type to use in the VDC. If not specified, will use one from the ones available in the location.
        required: False
    network:
        description:
          - The private network to create in the VDC.
        required: False
    vmsSoft:
        description:
          - Set soft limit for VMs.
        required: False
    vmsHard:
        description:
          - Set hard limit for VMs.
        required: False
    vlansSoft:
        description:
          - Set soft limit for VLANs.
        required: False
    vlansHard:
        description:
          - Set hard limit for VLANs.
        required: False
    publicIpsSoft:
        description:
          - Set soft limit for public IPs.
        required: False
    publicIpsHard:
        description:
          - Set hard limit for public IPs.
        required: False
    ramSoft:
        description:
          - Set soft limit for RAM.
        required: False
    ramHard:
        description:
          - Set hard limit for RAM.
        required: False
    cpuSoft:
        description:
          - Set soft limit for vCPUs.
        required: False
    cpuHard:
        description:
          - Set hard limit for vCPUs.
        required: False
    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create VDC 'vdc1'
  abiquo_vdc:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: vdc1
    location: "{{ location }}"
    network:
        default: yes

- name: Create VDC 'vdc2'
  abiquo_vdc:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: vdc2
    location: "{{ location }}"
    network:
        name: vdc1_default_net
        address: 1.2.3.0
        mask: 24
        gateway: 1.2.3.4
        primaryDNS: 8.8.8.8
        secondaryDNS: 1.1.1.1

'''


def core(module):
    name = module.params['name']
    enterprise = module.params['enterprise']
    location = module.params['location']
    hypervisortype = module.params['hypervisortype']
    network = module.params['network']
    vmsSoft = module.params['vmsSoft']
    vmsHard = module.params['vmsHard']
    vlansSoft = module.params['vlansSoft']
    vlansHard = module.params['vlansHard']
    publicIpsSoft = module.params['publicIpsSoft']
    publicIpsHard = module.params['publicIpsHard']
    ramSoft = module.params['ramSoft']
    ramHard = module.params['ramHard']
    cpuSoft = module.params['cpuSoft']
    cpuHard = module.params['cpuHard']
    state = module.params['state']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        c, vdcs = api.cloud.virtualdatacenters.get(
            headers={'Accept': 'application/vnd.abiquo.virtualdatacenters+json'})
        common.check_response(200, c, vdcs)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for vdc in vdcs:
        if vdc.name == name:
            if state == 'present':
                module.exit_json(
                    msg='VDC "%s"' %
                    name, changed=False, vdc=vdc.json)
            else:
                c, response = vdc.delete()
                try:
                    common.check_response(204, c, response)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='VDC "%s" deleted' % name, changed=True)

    if state == 'absent':
        module.exit_json(msg='VDC "%s"' % name, changed=False)
    else:
        location_lnk = common.getLink(location, 'location')

        if enterprise is None:
            enterprise = common.getMyEnterprise()
            enterprise_lnk = common.getLink(enterprise.json, 'edit')
        else:
            enterprise_lnk = enterprise
            enterprise_lnk['rel'] = 'enterprise'

        if hypervisortype is None:
            location = common.getDTO(location)
            code, hypervisortype = location.follow('hypervisortype').get()
            try:
                common.check_response(200, code, hypervisortype)
            except Exception as ex:
                module.fail_json(rc=code, msg=ex.message)
            hypervisortype = hypervisortype.name
        if network is None:
            network = common.getDefaultNetworkDict()

        vdc_json = {
            "links": [location_lnk, enterprise_lnk],
            "name": name,
            "hypervisorType": hypervisortype,
            "network": network,
            "vmsSoft": vmsSoft,
            "vmsHard": vmsHard,
            "vlansSoft": vlansSoft,
            "vlansHard": vlansHard,
            "publicIpsSoft": publicIpsSoft,
            "publicIpsHard": publicIpsHard,
            "ramSoft": ramSoft,
            "ramHard": ramHard,
            "cpuSoft": cpuSoft,
            "cpuHard": cpuHard
        }
        code, vdc = api.cloud.virtualdatacenters.post(
            headers={'Accept': 'application/vnd.abiquo.virtualdatacenter+json',
                     'Content-Type': 'application/vnd.abiquo.virtualdatacenter+json'},
            data=json.dumps(vdc_json)
        )
        try:
            common.check_response(201, code, vdc)
        except Exception as ex:
            if code == 406:  # NARS
                code, task = api.cloud.virtualdatacenters.post(
                    headers={'accept': 'application/vnd.abiquo.asynctask+json',
                             'content-type': 'application/vnd.abiquo.virtualdatacenter+json'},
                    data=json.dumps(vdc_json)
                )

                try:
                    attempts = module.params.get('abiquo_max_attempts')
                    delay = module.params.get('abiquo_retry_delay')

                    common.check_response(201, code, task)
                    task = common.track_async_task(task, attempts, delay)
                    if not common.async_task_status_ok(task):
                        raise Exception("Create VDC failed. Check events.")
                    code, vdc = task.follow('owner').get()
                    common.check_response(200, code, vdc)
                except Exception as e:
                    module.fail_json(rc=code, msg=e.message)
            else:
                module.fail_json(rc=code, msg=ex.message)
        module.exit_json(
            msg='VDC "%s" created' %
            name, changed=True, vdc=vdc.json)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        enterprise=dict(default=None, required=False, type='dict'),
        location=dict(default=None, required=True, type='dict'),
        hypervisortype=dict(default=None, required=False),
        network=dict(default=None, required=False, type='dict'),
        vmsSoft=dict(default=0, required=False),
        vmsHard=dict(default=0, required=False),
        vlansSoft=dict(default=0, required=False),
        vlansHard=dict(default=0, required=False),
        publicIpsSoft=dict(default=0, required=False),
        publicIpsHard=dict(default=0, required=False),
        ramSoft=dict(default=0, required=False),
        ramHard=dict(default=0, required=False),
        cpuSoft=dict(default=0, required=False),
        cpuHard=dict(default=0, required=False),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_datacenter: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
