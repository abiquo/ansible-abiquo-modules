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
module: abiquo_remote_repository
short_description: Manage abiquo_remote_repository in an Abiquo cloud platform
description:
    - Manage abiquo_remote_repository in an Abiquo cloud platform private datacenter.
    - Allows to add and remove abiquo_remote_repository from a datacenter.
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
    url:
        description:
          - URL of the `ovfindex.xml` file of the repository
        required: True
    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

  - name: Create remote repository
    abiquo_remote_repository:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      url: https://abq-repo-test.s3.amazonaws.com/ovfindex.xml

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def core(module):
    url = module.params['url']
    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    c, user = api.login.get()
    try:
        common.check_response(200, c, user)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    c, enterprise = user.follow('enterprise').get()
    try:
        common.check_response(200, c, enterprise)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    c, remote_repos = enterprise.follow('appslib/templateDefinitionLists').get()
    try:
        common.check_response(200, c, remote_repos)
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

    remote_repo = filter(lambda x: x.url == url, remote_repos)
    if len(remote_repo) > 0:
        remote_repo = remote_repo[0]
    else:
        remote_repo = None

    if remote_repo is not None:
        if state == 'present':
            module.exit_json(msg='Remote repository with url "%s" already exists' % url, changed=False, repo=remote_repo.json)
        else:
            c, rresp = remote_repo.delete()
            try:
                common.check_response(204, c, rresp)
            except Exception as ex:
                module.fail_json(rc=c, msg=ex.message)
            module.exit_json(msg='Remote repository with url "%s" deleted' % url, changed=True)
    else:
        if state == 'absent':
            module.exit_json(msg='Remote repository with url "%s" does not exist' % url, changed=False)
        else:
            c, rrepo = enterprise.follow('appslib/templateDefinitionLists').post(
                headers={'accept': 'application/vnd.abiquo.templatedefinitionlist+json','content-type': 'text/plain'},
                data=url
            )
            try:
                common.check_response(201, c, rrepo)
            except Exception as ex:
                module.fail_json(rc=c, msg=ex.message)
            module.exit_json(msg='Remote repository with url "%s" created' % url, changed=True, repo=rrepo.json)

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
            url=dict(default=None, required=True),
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
        module.fail_json(msg='Unanticipated error running abiquo_remote_repository: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
