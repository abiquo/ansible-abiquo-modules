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
import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    name = module.params['name']
    provider = module.params['provider']
    region = module.params['region']
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    try:
        c, pcrs = api.admin.publiccloudregions.get(headers={'Accept': 'application/vnd.abiquo.publiccloudregions+json'})
        common.check_response(200, c, pcrs)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for pcr in pcrs:
        if pcr.name == name:
            if state == 'present':
                module.exit_json(msg='Public cloud region %s from provider %s already exists' % (region, provider), changed=False, pcr=pcr.json)
            else:
                c, pcrresp = pcr.delete()
                try:
                    common.check_response(204, c, pcrresp)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='Public cloud region %s from provider %s deleted' % (region, provider), changed=True)

    if state == 'absent':
        module.exit_json(msg='Public cloud region %s from provider %s does not exist' % (region, provider), changed=False)
    else:
        reg = common.lookup_region(provider, region)
        if reg is None:
            module.fail_json(rc=1, msg='Region %s in provider %s has not been found!' % (provider, region))
        reglnk = reg._extract_link('self')
        reglnk['rel'] = 'region'
        pcrjson = {
            'name': name,
            'provider': provider,
            'links': [ reglnk ]
        }
        c, pcr = api.admin.publiccloudregions.post(
            headers={'accept': 'application/vnd.abiquo.publiccloudregion+json','content-Type': 'application/vnd.abiquo.publiccloudregion+json'},
            data=json.dumps(pcrjson)
        )
        try:
            common.check_response(201, c, pcr)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg='Public cloud region %s from provider %s created' % (region, provider), changed=True, pcr=pcr.json)

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
            provider=dict(default=None, required=True),
            region=dict(default=None, required=True),
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
        module.fail_json(msg='Unanticipated error running abiquo_public_cloud_region: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
