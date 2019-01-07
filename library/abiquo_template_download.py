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
module: abiquo_template_download
short_description: Download templates from a remote repository in an Abiquo cloud platform
description:
    - Download templates from a remote repository in an Abiquo cloud platform.
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
    template_name:
        description:
          - Name of the template definition to download
        required: True
    remote_repository_url:
        description:
          - URL of the remote repository to download the template from
        required: True
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

  - name: Download templates
    abiquo_template:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      datacenter: some-dc
      remote_repository_url: https://abq-repo-test.s3.amazonaws.com/ovfindex.xml
      template_name: Alpine Linux
      state: download

  - name: Enable cloud init in templates
    abiquo_template:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      datacenter: some-dc
      remote_repository_url: https://abq-repo-test.s3.amazonaws.com/ovfindex.xml
      template_name: Alpine Linux
      attribs:
        guestSetup: CLOUD_INIT

'''

# import module snippets
import traceback, json, time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import datacenter
from ansible.module_utils.abiquo import template

def core(module):
    template_name = module.params['template_name']
    remote_repository_url = module.params['remote_repository_url']
    dc_name = module.params['datacenter']
    state = module.params['state']

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

    try:
        tpl = datacenter.find_template(module)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    if tpl is not None:
        if state == 'present' or state == 'download':
            tpl_link = tpl._extract_link('edit')
            if module.params.get('attribs') is not None:
                try:
                    tpl = template.update(tpl, module)
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                module.exit_json(msg='Template %s updated in datacenter %s' % (template_name, dc_name), changed=True, template=tpl.json, template_link=tpl_link)
            module.exit_json(msg='Template %s already exists in datacenter %s' % (template_name, dc_name), changed=False, template=tpl.json, template_link=tpl_link)
        else:
            try:
                template.delete(tpl)
            except Exception as ex:
                module.fail_json(msg=ex.message)
            module.exit_json(msg='Template %s in datacenter %s deleted' % (template_name, dc_name), changed=True)
    else:
        if state == 'absent':
            module.exit_json(msg='Template %s in datacenter %s does not exist' % (template_name, dc_name), changed=False)
        elif state == 'download':
            try:
                task = template.download(module, dc_name, remote_repository_url, template_name)
            except Exception as ex:
                module.fail_json(msg=ex.message)

            if module.params.get('wait_for_download'):
                try:
                    task = common.track_task(task, module.params.get('max_attempts'), module.params.get('retry_delay'))
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                except ValueError as ve:
                    module.fail_json(msg="Track download task timed out.")

                if task.state == 'FINISHED_SUCCESSFULLY':
                    tpl = template.lookup_result(task)
                    tpl_link = tpl._extract_link('edit')
                    module.exit_json(msg='Template %s downloaded in datacenter %s' % (template_name, dc_name), changed=True, template=tpl.json, template_link=tpl_link)
                elif task.state == 'FINISHED_UNSUCCESSFULLY':
                    module.fail_json(msg="Download task failed, check events.")
            else:
                module.exit_json(msg='Template %s downloading in datacenter %s' % (template_name, datacenter), changed=True)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        template_name=dict(default=None, required=True),
        remote_repository_url=dict(default=None, required=True),
        datacenter=dict(default=None, required=True),
        attribs=dict(default=None, required=False, type=dict),
        wait_for_download=dict(default=False, required=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent', 'download']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_template_download: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
