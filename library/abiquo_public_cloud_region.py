#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

# from __future__ import absolute_import, division, print_function
# __metaclass__ = type


import json
import traceback
from ansible.module_utils.abiquo import pcr
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_public_cloud_region
short_description: Manage public cloud regions in an Abiquo cloud platform
description:
    - Manage public cloud regions in an Abiquo cloud platform
    - Allows to add and remove public cloud regions from a platform
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
    cloud_provider:
        description:
          - Name of the cloud provider of the region to add
        required: True
    region:
        description:
          - Name of the region to add
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

# import module snippets


def core(module):
    name = module.params.get('name')
    provider = module.params.get('provider')
    region = module.params.get('region')
    state = module.params.get('state')

    try:
        pcrs = pcr.list(module)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for pubreg in pcrs:
        if pubreg.name == name:
            if state == 'present':
                pcr_link = pubreg._extract_link('edit')
                module.exit_json(
                    msg='Public cloud region %s from provider %s already exists' %
                    (region, provider), changed=False, pcr=pubreg.json, pcr_link=pcr_link)
            else:
                try:
                    pcr.delete(pubreg)
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                module.exit_json(
                    msg='Public cloud region %s from provider %s deleted' %
                    (region, provider), changed=True)

    if state == 'absent':
        module.exit_json(
            msg='Public cloud region %s from provider %s does not exist' %
            (region, provider), changed=False)
    else:
        reg = pcr.lookup_region(module)
        if reg is None:
            module.fail_json(
                rc=1, msg='Region %s in provider %s has not been found!' %
                (provider, region))

        try:
            pcreg = pcr.create_pcr(reg, module)
            pcr_link = pcreg._extract_link('edit')
        except Exception as ex:
            module.fail_json(msg=ex.message)
        module.exit_json(
            msg='Public cloud region %s from provider %s created' %
            (region, provider), changed=True, pcr=pcreg.json, pcr_link=pcr_link)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        provider=dict(default=None, required=True),
        region=dict(default=None, required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_public_cloud_region: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
