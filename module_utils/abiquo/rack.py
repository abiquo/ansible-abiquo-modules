import json

from common import AbiquoCommon
from abiquo.client import check_response
import datacenter


def get_machines(rack):
    code, machines = rack.follow('machines').get()
    check_response(200, code, machines)

    all_machines = []
    for machine in machines:
        all_machines.append(machine)

    return all_machines


def delete_machine(machine):
    code, resp = machine.delete()
    check_response(204, code, resp)


def create_machine(rack, module):
    # Get Service Network service type:
    code, dc = rack.follow('datacenter').get()
    check_response(200, code, dc)

    stypes = datacenter.get_network_service_types(dc)
    stypesf = filter(lambda x: x.name == 'Service Network', stypes)
    if len(stypesf) == 0:
        return 1, "Could not find 'Service Network' service type."
    stype = stypesf[0]
    stypelnk = stype._extract_link('edit')
    stypelnk['rel'] = 'networkservicetype'

    # Discover the machine.
    disc_query_params = {
        'user': module.params.get('user'),
        'password': module.params.get('password'),
        'hypervisor': module.params.get('hyp_type'),
        'ip': module.params.get('ip'),
        'port': module.params.get('port'),
    }

    hyp = datacenter.discover(dc, disc_query_params)

    # Set the network type
    for nic in hyp['networkInterfaces']['collection']:
        if nic['name'] == module.params.get('service_nic'):
            nic['links'].append(stypelnk)

    # Enable datastore
    if module.params.get('datastore_name') is None:
        dsf = filter(lambda x: x['rootPath'] == module.params.get(
            'datastore_root'), hyp['datastores']['collection'])
    else:
        dsf = filter(lambda x: x['name'] == module.params.get(
            'datastore_name'), hyp['datastores']['collection'])
    ds = dsf[0]
    ds['enabled'] = True
    if module.params.get('datastore_dir') is not None:
        ds['directory'] = module.params.get('datastore_dir')

    # Set credentials
    hyp['user'] = module.params.get('user')
    hyp['password'] = module.params.get('password')

    # Create the host
    code, machine = rack.follow('machines').post(
        headers={'accept': 'application/vnd.abiquo.machine+json',
                 'content-type': 'application/vnd.abiquo.machine+json'},
        data=json.dumps(hyp))
    check_response(201, code, machine)
    return machine
