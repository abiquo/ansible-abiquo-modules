import time, json

from abiquo.client import check_response
from common import AbiquoCommon

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

def undeploy_vapp(vapp, module):
    common = AbiquoCommon(module)
    attempts = module.params.get('max_attempts')
    delay = module.params.get('retry_delay')
    force = module.params.get('force')

    request_dict = {
        "forceEnterpriseSoftLimits" : force,
        "forceVdcLimits" : force,
        "forceUndeploy" : force
    }

    code, undeploy_task = vapp.follow('undeploy').post(
        headers={'accept': 'application/vnd.abiquo.acceptedrequest+json',
                'content-Type': 'application/vnd.abiquo.virtualmachinetask+json'},
        data=json.dumps(request_dict)
    )
    check_response(202, code, undeploy_task)

    # Wait for the vApp to unlock
    task = common.track_task(undeploy_task, attempts, delay)

    if task.state != "FINISHED_SUCCESSFULLY":
        raise Exception("Undeploy failed on vApp '%s'. Check events." % vapp.name)

    return vapp
