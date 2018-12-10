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
module: abiquo_license
short_description: Manage license keys in an Abiquo cloud platform
description:
    - Manage license keys in an Abiquo cloud platform
    - Allows to add and remove license keys from a platform
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
    code:
        description:
          - License code to be added to Abiquo
        required: True
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Set license in Abiquo
    abiquo_license:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      code: suppaduppalicensekey

'''

# import module snippets
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    code = module.params['code']
    codeout = "%s..." % code[0:10]
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    try:
        c, licenses = api.config.licenses.get(headers={'Accept': 'application/vnd.abiquo.licenses+json'})
        common.check_response(200, c, licenses)
    except Exception as ex:
        module.fail_json(rc=code, msg=ex.message)

    for lic in licenses:
        if lic.code == code:
            if state == 'present':
                module.exit_json(msg=codeout, changed=False)
            else:
                c, licresp = lic.delete()
                try:
                    common.check_response(204, c, licresp)
                except Exception as ex:
                    module.fail_json(rc=c, msg=ex.message)
                module.exit_json(msg='License "%s" deleted' % codeout, changed=True)

    if state == 'absent':
        module.exit_json(msg=codeout, changed=False)
    else:
        c, lic = api.config.licenses.post(
            headers={'Accept': 'application/vnd.abiquo.license+json','Content-Type': 'application/vnd.abiquo.license+json'},
            data='{ "code": "%s" }' % code
        )
        try:
            common.check_response(201, c, lic)
        except Exception as ex:
            module.fail_json(rc=c, msg=ex.message)
        module.exit_json(msg=codeout, changed=True, lic=lic.json)

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
            code=dict(default=None, required=True),
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
        module.fail_json(msg='Unanticipated error running abiquo_license: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
