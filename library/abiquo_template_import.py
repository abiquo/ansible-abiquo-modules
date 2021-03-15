#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import traceback
from ansible.module_utils.abiquo import template as template_module
from ansible.module_utils.abiquo import pcr as pcr_module
from ansible.module_utils.abiquo import enterprise as enterprise_module
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_template_import
short_description: Import templates from a remote provider in an Abiquo cloud platform
description:
    - Download templates from a remote repository in an Abiquo cloud platform.
version_added: "2.7"
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


    template_id:
        description:
          - ID of the template as supported by the plugin
        required: True
    datacenter:
        description:
          - Name of the datacenter where the template should be downloaded
        required: True

    state:
        description:
          - State of the datacenter
        required: True
        choices: ["import", "absent"]
        default: "import"
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


def lookup_dc_enterprise(module):
    enterprise_link = module.params.get('enterprise')
    datacenter_link = module.params.get('datacenter')

    enterprise = enterprise_module.find_by_link(module, enterprise_link)
    datacenter = pcr_module.find_by_link(module, datacenter_link)

    return datacenter, enterprise


def delete_template(module):
    datacenter, enterprise = lookup_dc_enterprise(module)

    if datacenter is None or enterprise is None:
        module.fail_json(msg="Datacenter or enterprise was not found.")

    template_id = module.params.get('template_id')
    try:
        dc_repo = enterprise_module.get_repo_for_dc(enterprise, datacenter)
        template = template_module.find_by_disk_path(dc_repo, template_id)
    except Exception as e:
        module.fail_json(msg=e.message)

    if template is None:
        module.fail_json(
            msg="Template ID %s already deleted" %
            template_id, changed=False)
    else:
        try:
            template_module.delete(template)
            module.exit_json(
                msg="Template ID %s deleted." %
                template_id, changed=True)
        except Exception as e:
            module.fail_json(msg=e.message)


def update_template(module):
    datacenter, enterprise = lookup_dc_enterprise(module)

    if datacenter is None or enterprise is None:
        module.fail_json(msg="Datacenter or enterprise was not found.")

    template_id = module.params.get('template_id')
    try:
        dc_repo = enterprise_module.get_repo_for_dc(enterprise, datacenter)
        template = template_module.find_by_disk_path(dc_repo, template_id)
    except Exception as e:
        module.fail_json(msg=e.message)

    if template is None:
        module.exit_json(
            msg="Template ID %s does not exist." %
            template_id, changed=False)
    else:
        try:
            template = template_module.update(template, module)
            template_link = template._extract_link('edit')
            module.exit_json(
                msg="Template ID %s updated." %
                template_id,
                changed=True,
                template=template.json,
                template_link=template_link)
        except Exception as e:
            module.fail_json(msg=e.message)


def import_template(module):
    datacenter, enterprise = lookup_dc_enterprise(module)

    if datacenter is None or enterprise is None:
        module.fail_json(msg="Datcenter or enterprise was not found.")

    template_id = module.params.get('template_id')
    try:
        dc_repo = enterprise_module.get_repo_for_dc(enterprise, datacenter)
        template = template_module.find_by_disk_path(dc_repo, template_id)
    except Exception as e:
        module.fail_json(msg=e.message)

    if template is None:
        try:
            template = template_module.search_by_id(dc_repo, template_id)
        except Exception as e:
            module.fail_json(msg=e.message)

        if template is None:
            module.fail_json(
                msg="Template with ID '%s' could not be found in the provider." %
                template_id)

        try:
            imported_template = template_module.import_template(
                dc_repo, template)
        except Exception as e:
            module.fail_json(msg=e.message)

        imported_template_link = imported_template._extract_link('edit')
        module.exit_json(
            msg="Template ID %s imported" %
            template_id,
            changed=True,
            template=imported_template.json,
            template_link=imported_template_link)
    else:
        template_link = template._extract_link('edit')
        module.exit_json(
            msg="Template ID %s already imported" %
            template_id,
            changed=False,
            template=template.json,
            template_link=template_link)


def core(module):
    state = module.params.get('state')
    if state == 'present':
        import_template(module)
    elif state == 'update':
        update_template(module)
    else:
        delete_template(module)


def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        template_id=dict(default=None, required=True),
        datacenter=dict(default=None, required=True, type='dict'),
        enterprise=dict(default=None, required=True, type='dict'),
        attribs=dict(default=None, required=False, type=dict),
        state=dict(default='present', choices=['present', 'absent', 'update']),
    )
    module = AnsibleModule(
        argument_spec=arg_spec
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(
            msg='Unanticipated error running abiquo_template_import: %s' %
            to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
