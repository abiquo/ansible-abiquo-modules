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

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    template_name = module.params['template_name']
    remote_repository_url = module.params['remote_repository_url']
    datacenter = module.params['datacenter']
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    c, template = common.find_template(datacenter, template_name)
    if c != 0:
        module.fail_json(rc=c, msg=template)

    if template is not None:
        if state == 'present' or state == 'download':
            if module.params['attribs'] is not None:
                for k, v in module.params['attribs'].iteritems():
                    setattr(template, k, v)
                    c, template = template.put()
                    try:
                        common.check_response(200, c, template)
                    except Exception as ex:
                        module.fail_json(rc=c, msg=ex.message)
            module.exit_json(msg='Template %s already exists in datacenter %s' % (template_name, datacenter), changed=False)
        else:
            c, tresp = template.delete()
            try:
                common.check_response(204, c, tresp)
            except Exception as ex:
                module.fail_json(rc=c, msg=ex.message)
            module.exit_json(msg='Template %s in datacenter %s deleted' % (template_name, datacenter), changed=True)
    else:
        if state == 'absent':
            module.exit_json(msg='Template %s in datacenter %s does not exist' % (template_name, datacenter), changed=False)
        elif state == 'download':
            c, download = common.download_template(datacenter, remote_repository_url, template_name)
            try:
                common.check_response(202, c, download)
            except Exception as ex:
                module.fail_json(rc=c, msg=ex.message)

            if module.params['wait_for_download']:
                common.enable_debug()
                l = common.fix_link(download, 'status', type='application/vnd.abiquo.task+json')
                c, task = l.get()
                while True:
                    try:
                        common.check_response(200, c, task)
                    except Exception as ex:
                        module.fail_json(rc=c, msg=ex.message)
                    if task.state == 'FINISHED_SUCCESSFULLY':
                        module.exit_json(msg='Template %s downloaded in datacenter %s' % (template_name, datacenter), changed=True)
                    elif task.state == 'FINISHED_UNSUCCESSFULLY':
                        module.fail_json(rc=1, msg="Download task failed, check events.")
                    else:
                        time.sleep(10)
                        t = common.fix_link(task, 'self', type='application/vnd.abiquo.task+json')
                        c, task = t.get()
            else:
                module.exit_json(msg='Template %s downloading in datacenter %s' % (template_name, datacenter), changed=True)

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
            template_name=dict(default=None, required=True),
            remote_repository_url=dict(default=None, required=True),
            datacenter=dict(default=None, required=True),
            attribs=dict(default=None, required=False, type=dict),
            wait_for_download=dict(default=False, required=False),
            state=dict(default='present', choices=['present', 'absent', 'download']),
        ),
    )

    if module.params['api_user'] is None and module.params['app_key'] is None:
        module.fail_json(msg="either basic auth or OAuth credentials are required")

    if not 'verify' in module.params:
        module.params['verify'] = True

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_template_download: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
