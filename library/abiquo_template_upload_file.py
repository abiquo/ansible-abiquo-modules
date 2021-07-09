#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

# from __future__ import absolute_import, division, print_function
# __metaclass__ = type


import time
import json
import traceback
from ansible.module_utils.abiquo import template
from ansible.module_utils.abiquo import datacenter
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_template_upload_file
short_description: Upload OVA files in an Abiquo cloud platform
description:
    - Upload OVA files in an Abiquo cloud platform
version_added: "2.4"
author: 
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
    datacenter:
        description:
          - Name of the datacenter where the template should be downloaded
        required: True
    wait_for_download:
        description:
          - If state is download, whether or not to wait for the template to be fully downloaded before moving on.
        required: False
        default: no
    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''
  - name: Upload templates
    abiquo_template:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      datacenter: some-dc
      template_file_path: /home/xrins/file.ova
      state: present
'''

# import module snippets


def core(module):
    dc_name = module.params['datacenter']
    state = module.params['state']
    template_file_path = module.params['template_file_path']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    datacenters = datacenter.list(module)
    dc = filter(lambda x: x.name == dc_name, datacenters)
    if len(dc) == 0:
        module.fail_json(rc=1, msg='Datcenter "%s" has not been found!' % dc)
    dc = dc[0]

    if state == 'present' or state == 'upload':
        tpl_link = tpl._extract_link('edit')
        if module.params.get('attribs') is not None:
            try:
                tpl = template.upload(template_file_path, module)
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(
                msg='Template %s updated in datacenter %s' %
                (template_name,
                    dc_name),
                changed=True,
                template=tpl.json,
                template_link=tpl_link)
        module.exit_json(
            msg='Template %s already exists in datacenter %s' %
            (template_name,
                dc_name),
            changed=False,
            template=tpl.json,
            template_link=tpl_link)



def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        template_name=dict(default=None, required=True),
        datacenter=dict(default=None, required=True),
        attribs=dict(default=None, required=False, type=dict),
        wait_for_download=dict(default=False, required=False, type='bool'),
        template_file_path=dict(default={}, required=False),
        state=dict(
            default='present',
            choices=[
                'present',
                'upload']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_template_upload_file: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()