#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from logging import raiseExceptions
import traceback
from ansible.module_utils.abiquo import template
from ansible.module_utils.abiquo import datacenter
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from abiquo.client import check_response

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: abiquo_template_upload_ova
short_description: Upload OVA files in an Abiquo cloud platform
description:
    - Upload OVA files in an Abiquo cloud platform
version_added: "2.4"
author: 
requirements:
    - "python >= 2.6"
    - "abiquo-api >= 0.1.13"
options:
    template_name:
        description:
          - Define the uploaded template name
        required: True
    guest_setup_type:
        description:
          - Define the gues setup type of the template.
        choices: ["HYPERVISOR_TOOLS", "CLOUD_INIT"]
        required: True
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
    dc_id:
        description:
          - ID of the datacenter repository where the template should be uploaded
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
      dc_id: 4
      template_file_path: /home/xrins/file.ova
      state: present

'''


def core(module):
    template_file_path = module.params['template_file_path']
    enterprise_id = module.params['enterprise_id']
    api_user = module.params['abiquo_api_user']
    api_pass = module.params['abiquo_api_pass']
    dc_id = module.params['dc_id']
    guest_setup_type = module.params['guest_setup_type']
    template_name = module.params['template_name']

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)
    api = common.client

    try:
        am_uri = get_am_uri(api, dc_id)
        location = upload_ova(am_uri, api_user, api_pass, enterprise_id, template_file_path)
        template_object = edit_uploaded_ova(api, enterprise_id, dc_id, location, guest_setup_type, template_name)
        module.exit_json(
            msg='Template with ID {} uploaded'.format(template_object.id),
            changed=True,
        )
    except Exception as ex:
        module.fail_json(msg=ex)

def get_am_uri(api, dc_id):
    code, remoteservices = api.admin.datacenters(dc_id).remoteservices.get()
    check_response(200, code, remoteservices)
    for remoteservice in remoteservices:
        if remoteservice.type == "APPLIANCE_MANAGER":
            return remoteservice.uri
    raise Exception("Appliance manager not found")

def upload_ova(am_url, api_user, api_pass, enterprise_id, template_file_path):
    template_response = template.upload(am_url, api_user, api_pass, enterprise_id, template_file_path)
    if template_response.status_code == 201:
        return template_response.headers['Location']
    raise Exception("AM response: {}".format(template_response.status_code))

def get_first_element(template_object):
    for template in template_object:
        return template
    raise Exception("Template object has no elements in collection")

def edit_uploaded_ova(api, enterprise_id, dc_id, location, guest_setup_type, template_name):
    template_disk_path = location.split('/templates/')[1]
    templates_object = template.find_template_by_path(api, enterprise_id, template_disk_path, dc_id)
    template_object = get_first_element(templates_object)
    if template_name is not None:
        template_object.name =  template_name
    if guest_setup_type is not None:
        template_object.guestSetup =  guest_setup_type
    c,response = template_object.put()
    if c == 200:
        return response
    raise Exception("API response when editing: {}".format(response.status_code))
    
def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        abiquo_api_url=dict(default=None, required=True),
        template_name=dict(default=None, required=False),
        enterprise_id=dict(default=None, required=True),
        dc_id=dict(default=None, required=True),
        template_file_path=dict(default=None, required=True),
        guest_setup_type=dict(
            default=None,
            choices=[
                'HYPERVISOR_TOOLS',
                'CLOUD_INIT'
            ]
        ),
        state=dict(
            default='present',
            choices=[
                'present'
            ]
        ),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_template_upload_ova: %s' %
                to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
