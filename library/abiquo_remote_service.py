#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_remote_service
short_description: Manage remote services in an Abiquo cloud platform
description:
    - Manage remote services in an Abiquo cloud platform
    - Allows to add and remove remote services from a platform
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
    rs_type:
        description:
          - Type of the remote service.
        required: True
    uri:
        description:
          - Full URL of the remote service
        required: True
    uuid:
        description:
          - UUID of the RS.
        required: False
    datacenters:
        description:
          - List of datacenters that will use this remote service. If empty, no datacenter will use it but it will still be created.
        required: False
        type: list
    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create APPLIANCE_MANAGER
  abiquo_remote_service:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    rs_type: APPLIANCE_MANAGER
    uri: "https://some.fqdn:443/am"
    datacenters:
      - someDC

'''

import traceback, json, re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import datacenter
from ansible.module_utils.abiquo import pcr

def core(module):
    uri = module.params['uri']
    rs_type = module.params['rs_type']
    uuid = module.params['uuid']
    state = module.params['state']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    links = []
    if 'datacenters' in module.params:
        datacenters = datacenter.list(module)
        dcs = filter(lambda x: x.name in module.params.get('datacenters'), datacenters)
        all_pcrs = pcr.list(module)
        pcrs = filter(lambda x: x.name in module.params.get('datacenters'), all_pcrs)
        
        for dc in dcs + pcrs:
            l = dc._extract_link('edit')
            linktype = re.search('abiquo\.(.*)\+', l['type'])
            if linktype:
                l['rel'] = linktype.group(1)
            else:
                l['rel'] = 'unknown'
            links.append(l)

    c, rss = api.admin.remoteservices.get(headers={'Accept': 'application/vnd.abiquo.remoteservices+json'})
    try:
        common.check_response(200, c, rss)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    for rs in rss:
        if rs.uri == uri:
            if state == 'present':
                module.exit_json(msg='RS %s at %s already exists' % (rs_type, uri), changed=False, rs=rs.json)
            else:
                c, rsresp = rs.delete()
                try:
                    common.check_response(204, c, rsresp)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='RS %s at %s deleted' % (rs_type, uri), changed=True)

    if state == 'absent':
        module.exit_json(msg='RS %s at %s does not exist' % (rs_type, uri), changed=False)
    else:
        rsjson = {
            'uri': uri,
            'type': rs_type,
            'links': links
        }
        if uuid is not None and uuid != '': rsjson['uuid'] = uuid 

        c, rs = api.admin.remoteservices.post(
            headers={'Accept': 'application/vnd.abiquo.remoteservice+json','Content-Type': 'application/vnd.abiquo.remoteservice+json'},
            data=json.dumps(rsjson)
        )
        try:
            common.check_response(201, c, rs)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg='RS %s at %s created' % (rs_type, uri), changed=True, rs=rs.json)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        uri=dict(default=None, required=True),
        rs_type=dict(default=None, required=True, type=str),
        datacenters=dict(default=None, required=False, type=list),
        uuid=dict(default=None, required=False),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_remote_service: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
