#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo import pricing_template
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_pricing_template
short_description: Manage princing templates in an Abiquo cloud platform
description:
    - Manage pricing templates in an Abiquo cloud platform
    - Allows to add and remove pricing templates from a platform
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
          - Name of the pricing template in Abiquo
        required: True
    description:
        description:
          - Description of the pricing template
        required: False
    standingChargePeriod:
        description:
          - Standing charge per charging period
        required: False
    showMinimumCharge:
        description:
          - If true, the platform will display the minimum charge
        required: False
    chargingPeriod:
        description:
          - Indicates the period of time to charge the user for
        required: False
    minimumChargePeriod:
        description:
          - Indicates the minimum period of time that a user will be charged for
        required: False
    showChangesBefore:
        description:
          - If true, the platform will display the charges before deployment
        required: False
    minimumCharge:
        description:
          - Minimum charge per minimum period
        required: False
    defaultTemplate:
        description:
          - If true, its the default pricing template
        required: False
    deployMessage:
        description:
          - The pricing estimate message
        required: False
    currency:
        description:
          - A link to the currency for the pricing template
        required: True

    state:
        description:
          - State of the pricing template
        required: True
        choices: ["present", "absent"]
        default: "present"
'''

EXAMPLES = '''

- name: Create pricing template 'price_std'
  abiquo_pricing_template:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    name: price_std
    description: price_std pricing template

'''


def pricing_template_present(module):
    p_template_name = module.params.get('name')
    p_template = pricing_template.find(module)

    if p_template is not None:
        # TODO UPDATE
        p_template_link = p_template._extract_link('edit')
        module.exit_json(
            msg='Pricing template "%s"' %
            p_template_name,
            changed=False,
            pricing_template=p_template.json,
            pricing_template_link=p_template_link)
    else:
        # Create
        try:
            p_template = pricing_template.create(module)
            p_template_link = p_template._extract_link('edit')
            module.exit_json(
                msg='Pricing template "%s" created' %
                p_template_name,
                changed=True,
                pricing_template=p_template.json,
                pricing_template_link=p_template_link)
        except Exception as ex:
            module.fail_json(msg=ex.message)


def pricing_template_absent(module):
    p_template_name = module.params.get('name')
    p_template = pricing_template.find(module)

    if p_template is None:
        module.exit_json(
            msg='Pricing template "%s" does not exist' %
            p_template_name, changed=False)
    else:
        try:
            pricing_template.delete(p_template)
            module.exit_json(
                msg='Pricing template "%s" deleted' %
                p_template_name, changed=True)
        except Exception as e:
            module.fail_json(msg=ex.message)


def core(module):
    state = module.params.get('state')

    if state == 'present':
        pricing_template_present(module)
    else:
        pricing_template_absent(module)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        name=dict(default=None, required=True),
        description=dict(default=None, required=False),
        standingChargePeriod=dict(default=0, required=False, type=int),
        showMinimumCharge=dict(default=None, required=False),
        chargingPeriod=dict(
            default=2,
            required=False,
            type=int),
        # 2 is for Day
        minimumChargePeriod=dict(default=0, required=False, type=int),
        showChangesBefore=dict(default=None, required=False),
        minimumCharge=dict(default=0, required=False, type=int),
        defaultTemplate=dict(default=None, required=False),
        deployMessage=dict(default=None, required=False),
        currency=dict(default=None, required=True, type=dict),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_pricing_template: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
