import time
import json

from abiquo.client import check_response
from ansible.module_utils.abiquo.common import AbiquoCommon


def find_vm_in_vdc(vapp, vm_label):
    code, vms = vapp.follow('virtualmachines').get()
    check_response(200, code, vms)

    all_vms = []
    for vm in vms:
        if vm.label == vm_label:
            return vm
    return None


def build_vm_links(module):
    links = []

    hardwareprofile_link = module.params.get('hardwareprofile')
    hardwareprofile_link['rel'] = 'hardwareprofile'
    links.append(hardwareprofile_link)
    template_link = module.params.get('template')
    template_link['rel'] = 'virtualmachinetemplate'
    links.append(template_link)

    return links


def create_vm(module):
    cpu = module.params.get('cpu')
    ram = module.params.get('ram')
    keymap = module.params.get('keymap')
    password = module.params.get('password')
    label = module.params.get('label')
    vdrpEnabled = module.params.get('vdrpEnabled')
    metadata = module.params.get('metadata')
    monitored = module.params.get('monitored')
    monitoringLevel = module.params.get('monitoringLevel')
    protected = module.params.get('protected')
    protectedCause = module.params.get('protectedCause')
    variables = module.params.get('variables')
    fqdn = module.params.get('fqdn')
    iconUrl = module.params.get('iconUrl')

    common = AbiquoCommon(module)

    vapp_link = module.params.get('vapp')
    vapp = common.get_dto_from_link(vapp_link)

    links = build_vm_links(module)

    vm_json = {
        "cpu": cpu,
        "ram": ram,
        "keymap": keymap,
        "password": password,
        "label": label,
        "vdrpEnabled": vdrpEnabled,
        "metadata": metadata,
        "monitored": monitored,
        "monitoringLevel": monitoringLevel,
        "protected": protected,
        "protectedCause": protectedCause,
        "variables": variables,
        "fqdn": fqdn,
        "iconUrl": iconUrl,
        "links": links
    }

    code, vm = vapp.follow('virtualmachines').post(
        headers={
            'accept': 'application/vnd.abiquo.virtualmachine+json',
            'content-type': 'application/vnd.abiquo.virtualmachine+json',
        },
        data=json.dumps(vm_json)
    )
    check_response(201, code, vm)

    return vm


def undeploy_vm(vm, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    code, undeploy_task = vm.follow('undeploy').post()
    check_response(202, code, undeploy_task)

    # Wait for the VM to unlock
    task = common.track_task(undeploy_task, attempts, delay)

    if task.state != "FINISHED_SUCCESSFULLY":
        raise Exception("Undeploy failed on VM '%s' (%s). Check events." % (vm.label, vm.name))

    return vm


def deploy_vm(vm, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    code, deploy_task = vm.follow('deploy').post()
    check_response(202, code, deploy_task)

    # Wait for the VM to unlock
    task = common.track_task(deploy_task, attempts, delay)

    if task.state != "FINISHED_SUCCESSFULLY":
        raise Exception("Deploy failed on VM '%s' (%s). Check events." % (vm.label, vm.name))

    return vm


def create_and_deploy_vm(module):
    vm = create_vm(module)
    vm = deploy_vm(vm, module)

    return vm


def validate_vm_config(module):
    common = AbiquoCommon(module)

    ##
    # Validate CPU,RAM vs HP
    #
    vapp_link = module.params.get('vapp')
    vapp = common.get_dto_from_link(vapp_link)

    code, vdc = vapp.follow('virtualdatacenter').get()
    check_response(200, code, vdc)

    code, location = vdc.follow('location').get()
    check_response(200, code, vdc)

    if location._extract_link('hardwareprofiles') is not None:
        ##
        # Need HWprofile
        #
        hp = module.params.get('hardwareprofile')
        if hp is None:
            return "This location requires the use of hardware profiles."

        code, hps = location.follow('hardwareprofiles').get(params={'has': hp['title']})
        check_response(200, code, hps)

        found = False
        for h in hps:
            if h.name == hp['title']:
                found = True

        if not found:
            return "Hardware profile '%s' does not exist or cannot be found." % hp['title']

    ##
    # Validation succeeded
    #
    return None


def delete_vm(vm, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    code, delete_task = vm.delete()
    check_response(202, code, delete_task)

    # Wait for the VM to unlock
    try:
        task = common.track_task(delete_task, attempts, delay)
        if task.state != "FINISHED_SUCCESSFULLY":
            raise Exception("Delete failed on VM '%s' (%s). Check events." % (vm.label, vm.name))

    except Exception as ex:
        if ex.message.startswith('HTTP(404)'):
            # VM has already been deleted.
            pass


def apply_vm_state(vm, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')
    state = module.params.get('state')

    state_dto = {}
    if state == 'shutdown':
        state_dto = {
            'state': 'OFF',
            'gracefulShutdown': True
        }
    else:
        state_dto = {
            'state': state.upper()
        }
    code, state_task = vm.follow('state').post(data=json.dumps(state_dto))
    check_response(202, code, state_task)

    # Wait for the VM to unlock
    task = common.track_task(state_task, attempts, delay)

    if task.state != "FINISHED_SUCCESSFULLY":
        raise Exception("State apply failed on VM '%s' (%s). Check events." % (vm.label, vm.name))

    return vm


def reset_vm(vm, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    code, reset_task = vm.follow('reset').post()
    check_response(202, code, reset_task)

    # Wait for the VM to unlock
    task = common.track_task(reset_task, attempts, delay)

    if task.state != "FINISHED_SUCCESSFULLY":
        raise Exception("Reset failed on VM '%s' (%s). Check events." % (vm.label, vm.name))

    return vm


def wait_vm_def_sync(vm, module):
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    for i in range(attempts):
        code, vm = vm.refresh()

        try:
            if vm.lastSynchronize:
                return vm
        except KeyError:
            time.sleep(delay)
    raise ValueError(
        'Exceeded %s attempts waiting for VM first sync for VM %s' %
        (attempts, vm.label))
