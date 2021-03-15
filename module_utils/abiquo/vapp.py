import time
import json

from abiquo.client import check_response
from ansible.module_utils.abiquo.common import AbiquoCommon


def find_vapp_in_vdc(vdc, vapp_name):
    code, vapps = vdc.follow('virtualappliances').get()
    check_response(200, code, vapps)

    for vapp in vapps:
        if vapp.name == vapp_name:
            return vapp
    return None


def create_vapp(module):
    common = AbiquoCommon(module)

    vdc = common.get_dto_from_link(module.params.get('vdc'))

    vapp_dict = {
        "name": module.params.get('name'),
        "iconUrl": module.params.get('iconUrl'),
        "description": module.params.get('description'),
        "restricted": module.params.get('restricted')
    }

    code, vapp = vdc.follow('virtualappliances').post(
        headers={'accept': 'application/vnd.abiquo.virtualappliance+json',
                 'content-Type': 'application/vnd.abiquo.virtualappliance+json'},
        data=json.dumps(vapp_dict)
    )
    common.check_response(201, code, vapp)
    return vapp


def delete_vapp(vapp, module):
    code, resp = vapp.delete()
    check_response(204, code, resp)


def deploy_vapp(vapp, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    request_dict = {}

    code, deploy_task = vapp.follow('deploy').post(
        headers={'accept': 'application/vnd.abiquo.acceptedrequest+json',
                 'content-Type': 'application/vnd.abiquo.virtualmachinetask+json'},
        data=json.dumps(request_dict)
    )
    check_response(202, code, deploy_task)

    # Wait for the vApp to unlock
    vapp = wait_vapp_state(vapp, module)

    return vapp


def undeploy_vapp(vapp, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')
    force = module.params.get('force')

    request_dict = {
        "forceEnterpriseSoftLimits": force,
        "forceVdcLimits": force,
        "forceUndeploy": force
    }

    code, undeploy_task = vapp.follow('undeploy').post(
        headers={'accept': 'application/vnd.abiquo.acceptedrequest+json',
                 'content-Type': 'application/vnd.abiquo.virtualmachinetask+json'},
        data=json.dumps(request_dict)
    )
    check_response(202, code, undeploy_task)

    # Wait for the vApp to unlock
    vapp = wait_vapp_state(vapp, module)

    return vapp


def wait_vapp_state(vapp, module):
    attempts = module.params.get('abiquo_max_attempts')
    delay = module.params.get('abiquo_retry_delay')

    for i in range(attempts):
        code, vapp = vapp.refresh()

        if vapp.state != 'LOCKED':
            return vapp
        else:
            time.sleep(delay)
    raise ValueError('Exceeded %s attempts waiting for vApp %s to become %s.' %
                     (attempts, vapp.name, module.params.get('state')))
