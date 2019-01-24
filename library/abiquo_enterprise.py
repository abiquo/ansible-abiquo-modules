#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_enterprise
short_description: Manage enterprises (tenants) in an Abiquo cloud platform
description:
    - Manage enterprises (tenants) in an Abiquo cloud platform
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
    name:
        description:
          - Enterprise name.
        required: True
    isReservationRestricted:
        description:
          - Enterprise is restricted to reserved hosts only.
        required: False
    workflow:
        description:
          - Enable or disable workflow for the enterprise
        required: False
    twoFactorAuthenticationMandatory:
        description:
          - Set or unset 2FA enforcement.
        required: False
    reseller:
        description:
          - Reseller.
        required: False
    keyNode:
        description:
          - keyNode
        required: False
    scope:
        description:
          - Default scope to set for new users in the enterprise.
        required: False
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create test tenant
  abiquo_enterprise:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: some_enterprise
    workflow: yes

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec

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
    
    name = module.params['name']
    isReservationRestricted = module.params['isReservationRestricted']
    workflow = module.params['workflow']
    twoFactorAuthenticationMandatory = module.params['twoFactorAuthenticationMandatory']
    reseller = module.params['reseller']
    keyNode = module.params['keyNode']

    state = module.params['state']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        c, enterprises = api.admin.enterprises.get(headers={'accept':'application/vnd.abiquo.enterprises+json'})
        common.check_response(200, c, enterprises)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for ent in enterprises:
        if ent.name == name:
            if state == 'present':
                ent_json = ent.json
                new_ent_json = common.build_json(module)
                if common.changes_required(ent_json, new_ent_json):
                    enterprise = common.update_dto(ent, module)
                    enterprise_link = enterprise._extract_link('edit')
                    module.exit_json(changed=True, enterprise=enterprise.json, enterprise_link=enterprise_link)
                else:
                    enterprise_link = ent._extract_link('edit')
                    module.exit_json(changed=False, enterprise=ent.json, enterprise_link=enterprise_link)
            else:
                code, entresp = ent.delete()
                try:
                    common.check_response(204, code, entresp)
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                module.exit_json(msg='Enterprise "%s" deleted' % ent.name, changed=True)

    if state == 'absent':
        module.exit_json(enterprise=ent.json, changed=False)
    else:
        enterprise_json = {
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
            'repositoryHardInMb': repositoryHardInMb,
            'name': name,
            'isReservationRestricted': isReservationRestricted,
            'workflow': workflow,
            'twoFactorAuthenticationMandatory': twoFactorAuthenticationMandatory,
            'reseller': reseller,
            'keyNode': keyNode
        }

        c, ent = api.admin.enterprises.post(
            headers={'accept':'application/vnd.abiquo.enterprise+json','content-type':'application/vnd.abiquo.enterprise+json'},
            data=json.dumps(enterprise_json)
        )
        try:
            common.check_response(201, c, ent)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(changed=True, enterprise=ent.json)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        vmsSoft=dict(default=0, required=False, type=int),
        vmsHard=dict(default=0, required=False, type=int),
        vlansSoft=dict(default=0, required=False, type=int),
        vlansHard=dict(default=0, required=False, type=int),
        publicIpsSoft=dict(default=0, required=False, type=int),
        publicIpsHard=dict(default=0, required=False, type=int),
        ramSoft=dict(default=0, required=False, type=int),
        ramHard=dict(default=0, required=False, type=int),
        cpuSoft=dict(default=0, required=False, type=int),
        cpuHard=dict(default=0, required=False, type=int),
        diskSoftLimitInMb=dict(default=0, required=False, type=int),
        diskHardLimitInMb=dict(default=0, required=False, type=int),
        storageSoftInMb=dict(default=0, required=False, type=int),
        storageHardInMb=dict(default=0, required=False, type=int),
        repositorySoftInMb=dict(default=0, required=False, type=int),
        repositoryHardInMb=dict(default=0, required=False, type=int),
        name=dict(default=None, required=True),
        isReservationRestricted=dict(default=False, required=False, type='bool'),
        workflow=dict(default=False, required=False, type='bool'),
        twoFactorAuthenticationMandatory=dict(default=False, required=False, type='bool'),
        reseller=dict(default=False, required=False, type='bool'),
        keyNode=dict(default=False, required=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_enterprise: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
