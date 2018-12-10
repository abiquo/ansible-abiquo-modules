#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_enterprise
short_description: Manage enterprises (tenants) in an Abiquo cloud platform
description:
    - Manage enterprises (tenants) in an Abiquo cloud platform
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
    
    availableVirtualDatacenters:
        description:
          - List of IDs of restricted VDCs for this user separated by commas
        required: False
        default: null
    email:
        description:
          - The contact e-mail address of the user for Abiquo messages
        required: False
        default: null
    locale:
        description:
          - Locale assigned to this user
        required: False
        default: en_US
    name:
        description:
          - User's real first name
        required: True
    nick:
        description:
          - User name / nickname. The username for login
        required: True
    password:
        description:
          - Password set for this user
        required: False
        default: null
    surname:
        description:
          - User's real last name
        required: False
        default: null
    active:
        description:
          - Flag indicating if the user is activated or not
        required: False
        default: True
    firstLogin:
        description:
          - Flag indicating if the user is logging in for the first time or not
        required: False
        default: False
    locked:
        description:
          - Flag indicating if the user is locked for too many failed password attempts
        required: False
        default: False
    publicSshKey:
        description:
          - User's public SSH key
        required: False
        default: null
    phoneNumber:
        description:
          - User's phone number. The platform does not validate the format and the expected formats are E.164 or RFC 3966 (for numbers with extensions)
        required: False
        default: null
    enterprise:
        description:
          - Enterprise where to create the user
        required: False
    role:
        description:
          - Role for the user
        required: False
    scope:
        description:
          - Scope for the user
        required: True
    state:
        description:
          - State of the license
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create test tenant
  abiquo_enterprise:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: some_enterprise
    workflow: yes

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo_common import AbiquoCommon

def update_user(user, module, api):
    common = AbiquoCommon(module)

    for k, v in module.params.items():
        user.__setattr__(k, v)

    try:
        c, ent = user.put()
        common.check_response(200, c, ent)
        return ent
    except Exception as ex:
        module.fail_json(rc=c, msg=ex.message)

def core(module):
    availableVirtualDatacenters = module.params['availableVirtualDatacenters']
    email = module.params['email']
    locale = module.params['locale']
    name = module.params['name']
    nick = module.params['nick']
    password = module.params['password']
    surname = module.params['surname']
    active = module.params['active']
    firstLogin = module.params['firstLogin']
    locked = module.params['locked']
    publicSshKey = module.params['publicSshKey']
    phoneNumber = module.params['phoneNumber']

    enterprise = module.params['enterprise']
    role = module.params['role']
    scope = module.params['scope']

    state = module.params['state']

    common = AbiquoCommon(module)
    api = common.client

    try:
        c, ent = api.admin.enterprises.get(id="%s" % enterprise['id'], headers={'accept':'application/vnd.abiquo.enterprise+json'})
        common.check_response(200, c, ent)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    try:
        c, users = ent.follow('users').get(params={'has':nick})
        common.check_response(200, c, users)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    for user in users:
        if user.nick == nick:
            if state == 'present':
                module.exit_json(changed=False, user=nick)
            elif state == 'update':
                user = update_user(user, module, api)
                module.exit_json(changed=True, user=user.json)
            else:
                c, userresp = user.delete()
                try:
                    common.check_response(204, c, userresp)
                except Exception as ex:
                    module.fail_json(msg=ex.message)
                module.exit_json(user=nick, changed=True)

    if state == 'absent':
        module.exit_json(user=nick, changed=False)
    else:
        user_json = {
            'availableVirtualDatacenters': availableVirtualDatacenters,
            'email': email,
            'locale': locale,
            'name': name,
            'nick': nick,
            'password': password,
            'surname': surname,
            'active': active,
            'firstLogin': firstLogin,
            'locked': locked,
            'publicSshKey': publicSshKey,
            'phoneNumber': phoneNumber
        }
        enterprise_lnk = common.getLink(enterprise, 'edit')
        enterprise_lnk['rel'] = 'enterprise'
        role_lnk = common.getLink(role, 'edit')
        role_lnk['rel'] = 'role'
        scope_lnk = common.getLink(scope, 'edit')
        scope_lnk['rel'] = 'scope'
        user_json['links'] = [ enterprise_lnk, role_lnk, scope_lnk ]

        c, usr = ent.follow('users').post(
            headers={'accept':'application/vnd.abiquo.user+json','content-type':'application/vnd.abiquo.user+json'},
            data=json.dumps(user_json)
        )
        try:
            common.check_response(201, c, usr)
        except Exception as ex:
            module.fail_json(msg=ex.message)
        module.exit_json(changed=True, user=usr.json)

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
            availableVirtualDatacenters=dict(default=None, required=False, type='list'),
            email=dict(default=None, required=True),
            locale=dict(default='en_US', required=False),
            name=dict(default=None, required=True),
            nick=dict(default=None, required=True),
            password=dict(default=None, required=False, no_log=True),
            surname=dict(default=None, required=False),
            active=dict(default=True, required=False, type='bool'),
            firstLogin=dict(default=False, required=False, type='bool'),
            locked=dict(default=False, required=False, type='bool'),
            publicSshKey=dict(default=None, required=False),
            phoneNumber=dict(default=None, required=False),
            enterprise=dict(default=None, required=True, type='dict'),
            role=dict(default=None, required=True, type='dict'),
            scope=dict(default=None, required=False, type='dict'),
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
        module.fail_json(msg='Unanticipated error running abiquo_user: %s' % to_native(e), exception=traceback.format_exc())

if __name__ == '__main__':
    main()
