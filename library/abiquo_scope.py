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
    name:
        description:
          - Name of the scope
        required: True
    scopeEntities:
        description:
          - Entities to be added to the scope. Use full json as returned by the Abiquo modules.
        required: False
    automaticAddDatacenter:
        description:
          - If true, all new datacenters created are added into this scope
        required: True
    automaticAddEnterprise:
        description:
          - If true, all new enterprises created are added into this scope
        required: True
    scopeParent:
        description:
          - Parent scope for this scope
        required: False
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create scope 'some_scope'
    abiquo_license:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      name: some_scope

- name: Create scope 'some_scope_2'
    abiquo_license:
      api_url: http://localhost:8009/api
      api_user: admin
      api_pass: xabiquo
      name: some_scope_2
      scopeEntities:
        - some_ent
        - some_dc

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import scope as common_scope

def update_scope(module):
    scope = common_scope.lookup_by_name(module)

    if scope is not None:
        try:
            scope = common_scope.update(module, scope)
            scope_link = scope._extract_link('edit')
            module.exit_json(msg="Scope '%s' updated." % scope.name, changed=True, scope=scope.json, scope_link=scope_link)
        except Exception as e:
            module.fail_json(msg=e.message)
    else:
        module.faile_json(msg="Scope '%s' does not exist." % module.params.get('name'), changed=False)

def create_scope(module):
    scope = common_scope.lookup_by_name(module)

    if scope is None:
        try:
            scope = common_scope.create(module)
        except Exception as e:
            module.fail_json(msg=e.message)
        scope_link = scope._extract_link('edit')
        module.exit_json(msg="Scope '%s' created." % scope.name, changed=True, scope=scope.json, scope_link=scope_link)
    else:
        scope_link = scope._extract_link('edit')
        module.exit_json(msg="Scope '%s' already exists." % scope.name, changed=False, scope=scope.json, scope_link=scope_link)

def delete_scope():
    scope = common_scope.lookup_by_name(module)

    if scope is not None:
        try:
            scope.delete()
            module.exit_json(msg="Scope '%s' deleted." % module.params.get('name'), changed=True)
        except Exception as e:
            module.fail_json(msg=e.message)
    else:
        module.exit_json(msg="Scope '%s' does not exist." % module.params.get('name'), changed=False)

def core(module):
    state = module.params.get('state')

    if state == 'present':
        create_scope(module)
    elif state == 'update':
        update_scope(module)
    else:
        delete_scope(module)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True, abiquo_updatable=True),
        scopeEntities=dict(default=None, required=False, type='list'),
        automaticAddDatacenter=dict(default=False, required=False, type='bool', abiquo_updatable=True),
        automaticAddEnterprise=dict(default=False, required=False, type='bool', abiquo_updatable=True),
        scopeParent=dict(default=None, required=False, type='dict'),
        state=dict(default='present', choices=['present', 'absent', 'update']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_scope: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
