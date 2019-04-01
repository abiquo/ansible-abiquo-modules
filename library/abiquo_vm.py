#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: abiquo_vm
short_description: Manage virtual machines in an Abiquo cloud platform
description:
    - Manage virtual machines in an Abiquo cloud platform
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


    cpu:
        description:
          - Integer Number of CPUs in the VM
        required: False
    ram:
        description:
          - Integer Amount of memory in the VM in megabytes
        required: False
    keymap:
        description:
          -  String  Keymap for the keyboard to be set on the VM
        required: False
    password:
        description:
          -  String  Remote acess password for opening a connection to a VM console
        required: False
    runlist:
        description:
          - runlistelements 
        required: False
    state:
        description:
          - VirtualMachineState Current VM state
        required: False
    label:
        description:
          - String  Friendly name of the VM. Displayed as the "Name" field in the user interface.
        required: False
    vdrpEnabled:
        description:
          - Boolean If true, the VM should accept remote access connections
        required: False
    metadata:
        description:
          -  Collection of String Object VM metadata used to store data for cloud-init, Chef, monitoring, etc.
        required: False
    monitored:
        description:
          - boolean Fetch metrics for this VM and enable monitoring features such as alarms, alerts, and action plans
        required: False
    monitoringLevel:
        description:
          - String  The monitoring level configured for the provider. Some providers such as AWS offer DETAILED and DEFAULT monitoring levels
        required: False
    protected:
        description:
          - boolean If true, the VM is protected by the administrator and the standard user cannot perform platform operations on the VM
        required: False
    protectedCause:
        description:
          -  String  The reason why the VM was protected
        required: False
    variables:
        description:
          - Collection of String String List of variables defined by name and value to send to the VM before first boot
        required: False
    creationTimestamp:
        description:
          - long  Timestamp of when the VM was created in milliseconds
        required: False
    fqdn:
        description:
          -  String  Fully qualified domain name of the VM. Can be entered and modified before deploy
        required: False
    iconUrl:
        description:
          - String  The URI of the icon of VM
        required: False



    hardwareprofile:
        description:
          - Link to the hardware profile to use for the VM.
        required: False



    template:
        description:
          - Link of the template to use to instantiate the VM
        required: True
    vapp:
        description:
          - Link of the vApp where to create the VM
        required: True
    

    wait_for_first_sync:
        description:
          - Wheter or not wait for the first VM definition sync on deploy
        required: False
        default: False


    state:
        description:
          - State of the datacenter
        required: True
        choices: ["present", "absent", "deploy", "undeploy", "on", "off", "reset", "shutdown"]
        default: "present"
'''

EXAMPLES = '''

- name: Create VM 'vm1'
  abiquo_vm:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    label: vm1
    cpu: 2
    ram: 8192
    template: "{{ some_template_link }}"
    vapp: "{{ some_vapp_link }}"

- name: Create VM 'vm2'
  abiquo_vm:
    api_url: http://localhost:8009/api
    api_user: admin
    api_pass: xabiquo
    label: vm2
    template: "{{ some_template_link }}"
    vapp: "{{ some_vapp_link }}"
    hwprofile: "{{ some_hp_link }}"

'''

import traceback, json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.abiquo.common import AbiquoCommon
from ansible.module_utils.abiquo.common import abiquo_argument_spec
from ansible.module_utils.abiquo import vm as virtualmachine

def lookup_vm_vapp(module):
    label = module.params.get('label')
    vapp_link = module.params.get('vapp')

    try:
        common = AbiquoCommon(module)
    except ValueError as ex:
        module.fail_json(msg=ex.message)

    vapp = None
    try:
        vapp = common.get_dto_from_link(vapp_link)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    vm = None
    try:
        vm = virtualmachine.find_vm_in_vdc(vapp, label)
    except Exception as ex:
        module.fail_json(msg=ex.message)

    return vm, vapp

def vm_present(module):
    vm, vapp = lookup_vm_vapp(module)

    if vm is None:
        validates = virtualmachine.validate_vm_config(module)
        if validates is not None:
            module.fail_json(msg=validates)

        try:
            vm = virtualmachine.create_vm(module)
        except ValueError as exv:
            module.fail_json(msg=exv.message)
        except Exception as ex:
            module.fail_json(msg=ex.message)

        vm_link = vm._extract_link('edit')
        module.exit_json(msg='VM "%s" created' % vm.label, changed=True, vm=vm.json, vm_link=vm_link)
    else:
        vm_link = vm._extract_link('edit')
        module.exit_json(msg='VM "%s" already exists' % vm.label, changed=False, vm=vm.json, vm_link=vm_link)

def vm_deploy(module):
    vm, vapp = lookup_vm_vapp(module)

    if vm is None:
        module.exit_json(msg='VM "%s" does not exist' % vm.label, changed=False)
    else:
        if vm.state != 'NOT_ALLOCATED':
            module.exit_json(msg='VM "%s" state "%s" does not allow deploy' % (vm.label, vm.state), changed=False)
        else:
            try:
                vm = virtualmachine.deploy_vm(vm, module)
                if module.params.get('wait_for_first_sync'):
                    vm = virtualmachine.wait_vm_def_sync(vm, module)
            except ValueError as exv:
                module.fail_json(msg=exv.message)
            except Exception as ex:
                module.fail_json(msg=ex.message)

            vm_link = vm._extract_link('edit')
            module.exit_json(msg='VM "%s" has been deployed' % vm.label, changed=True, vm=vm.json, vm_link=vm_link)

def vm_undeploy(module):
    vm, vapp = lookup_vm_vapp(module)

    if vm is None:
        module.exit_json(msg='VM "%s" does not exist' % vm.label, changed=False)
    else:
        if vm.state == 'NOT_ALLOCATED':
            module.exit_json(msg='VM "%s" is already undeployed.' % vm.label, changed=False)
        else:
            try:
                vm = virtualmachine.undeploy_vm(vm, module)
            except ValueError as exv:
                module.fail_json(msg=exv.message)
            except Exception as ex:
                module.fail_json(msg=ex.message)

            vm_link = vm._extract_link('edit')
            module.exit_json(msg='VM "%s" has been undeployed' % vm.label, changed=True, vm=vm.json, vm_link=vm_link)


def vm_absent(module):
    vm, vapp = lookup_vm_vapp(module)

    if vm is None:
        module.exit_json(msg='VM "%s" does not exist' % vm.label, changed=False)
    else:
        virtualmachine.delete_vm(vm, module)
        module.exit_json(msg='VM "%s" deleted' % vm.label, changed=True)

def vm_state(module):
    vm, vapp = lookup_vm_vapp(module)
    state = module.params.get('state')

    if vm is None:
        module.fail_json(msg="Requested VM cannot be found!")
    else:
        virtualmachine.apply_vm_state(vm, module)
        module.exit_json(msg='State %s applied to VM "%s"' % (state, vm.label), changed=True)

def vm_reset(module):
    vm, vapp = lookup_vm_vapp(module)

    if vm is None:
        module.fail_json(msg="Requested VM cannot be found!")
    else:
        virtualmachine.rese_vm(vm, module)
        module.exit_json(msg='VM %s reset successfully' % vm.label, changed=True)

def core(module):
    state = module.params['state']

    if state == 'present':
        vm_present(module)
    elif state == 'absent':
        vm_absent(module)
    elif state == 'reset':
        vm_reset(module)
    else:
        vm_state(module, state)

def main():
    arg_spec = abiquo_argument_spec()
    arg_spec.update(
        cpu=dict(default=None, required=False),
        ram=dict(default=None, required=False),
        keymap=dict(default=None, required=False),
        password=dict(default=None, required=False),
        label=dict(default=None, required=True),
        vdrpEnabled=dict(default=None, required=False),
        metadata=dict(default=None, required=False),
        monitored=dict(default=None, required=False),
        monitoringLevel=dict(default=None, required=False),
        protected=dict(default=None, required=False),
        protectedCause=dict(default=None, required=False),
        variables=dict(default={}, required=False, type='dict'),
        fqdn=dict(default=None, required=False),
        iconUrl=dict(default=None, required=False),
        hardwareprofile=dict(default=None, required=False, type='dict'),
        template=dict(default=None, required=True, type='dict'),
        vapp=dict(default=None, required=True, type='dict'),
        wait_for_first_sync=dict(default=False, required=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent', 'deploy', 'undeploy', 'on', 'off', 'reset', 'shutdown']),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running abiquo_vm: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
