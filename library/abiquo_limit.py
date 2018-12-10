#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_limit
short_description: Manage enterprise limit (datacenter to enterprise relation) an Abiquo cloud platform
description:
    - Manage enterprise limit (datacenter to enterprise relation) an Abiquo cloud platform
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
    enterprise:
        description:
          - Enterprise where to create the VDC as returned by abiquo_enterprise_facts module (or an equivalent dict)
        required: True
    location:
        description:
          - Datacenter or public cloud region to allow
        required: True
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
    diskSoftLimitInMb:
        description:
          - Set soft limit for hard disks.
        required: False
    diskHardLimitInMb:
        description:
          - Set hard limit for hard disks.
        required: False
    storageSoftInMb:
        description:
          - Set soft limit for external storage.
        required: False
    storageHardInMb:
        description:
          - Set hard limit for external storage.
        required: False
    repositorySoftInMb:
        description:
          - Set soft limit for repository space.
        required: False
    repositoryHardInMb:
        description:
          - Set hard limit for repository space.
        required: False
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Allow someDC to enterprise A
    abiquo_limit:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      location: "{{ someDC }}"
      enterprise: "{{ entA }}"

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
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
    diskSoftLimitInMb = module.params['diskSoftLimitInMb']
    diskHardLimitInMb = module.params['diskHardLimitInMb']
    storageSoftInMb = module.params['storageSoftInMb']
    storageHardInMb = module.params['storageHardInMb']
    repositorySoftInMb = module.params['repositorySoftInMb']
    repositoryHardInMb = module.params['repositoryHardInMb']
    
    enterprise = module.params['enterprise']
    location = module.params['location']

    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    location_lnk = common.getLink(location, 'edit')

    try:
        c, ent = api.admin.enterprises.get(id="%s" % enterprise['id'], headers={'Accept': 'application/vnd.abiquo.enterprise+json'})
        common.check_response(200, c, ent)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    try:
        c, lims = ent.follow('limits').get()
        common.check_response(200, c, lims)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for lim in lims:
        lim_location_link = lim._extract_link('location')
        if lim_location_link['href'] == location_lnk['href']:
            if state == 'present':
                module.exit_json(changed=False, msg=location['name'])
            else:
                c, limresp = lim.delete()
                try:
                    common.check_response(204, c, limresp)
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                module.exit_json(changed=True, msg=location['name'])

    if state == 'absent':
        module.exit_json(changed=False, msg=location['name'])
    else:
        location_lnk['rel'] = 'location'
        limit_json = {
            'links': [ location_lnk ],
            'vmsSoft': vmsSoft,
            'vmsHard': vmsHard,
            'vlansSoft': vlansSoft,
            'vlansHard': vlansHard,
            'publicIpsSoft': publicIpsSoft,
            'publicIpsHard': publicIpsHard,
            'ramSoft': ramSoft,
            'ramHard': ramHard,
            'cpuSoft': cpuSoft,
            'cpuHard': cpuHard,
            'diskSoftLimitInMb': diskSoftLimitInMb,
            'diskHardLimitInMb': diskHardLimitInMb,
            'storageSoftInMb': storageSoftInMb,
            'storageHardInMb': storageHardInMb,
            'repositorySoftInMb': repositorySoftInMb,
            'repositoryHardInMb': repositoryHardInMb
        }

        try:
            c, lim = ent.follow('limits').post(
                headers={'accept':'application/vnd.abiquo.limit+json','content-type':'application/vnd.abiquo.limit+json'},
                data=json.dumps(limit_json)
            )
            common.check_response(201, c, lim)
        except Exception as ex:
            module.fail_json(msg=ex.message)
        module.exit_json(changed=True, lim=lim.json)

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
            diskSoftLimitInMb=dict(default=0, required=False),
            diskHardLimitInMb=dict(default=0, required=False),
            storageSoftInMb=dict(default=0, required=False),
            storageHardInMb=dict(default=0, required=False),
            repositorySoftInMb=dict(default=0, required=False),
            repositoryHardInMb=dict(default=0, required=False),
            enterprise=dict(default=None, required=True, type='dict'),
            location=dict(default=None, required=True, type='dict'),
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
        module.fail_json(msg='Unanticipated error running abiquo_limit: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
