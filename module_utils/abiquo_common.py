from abiquo.client import Abiquo
from abiquo.client import check_response
from requests_oauthlib import OAuth1
from ansible.module_utils.basic import AnsibleModule
import json, urllib3, os, re

try:
    from http.client import HTTPConnection # py3
except ImportError:
    from httplib import HTTPConnection # py2

class AbiquoCommon(object):
    NETWORK_SYS_PROPS = [
        "client.network.numberIpAdressesPerPage",
        "client.network.defaultName",
        "client.network.defaultNetmask",
        "client.network.defaultAddress",
        "client.network.defaultGateway",
        "client.network.defaultPrimaryDNS",
        "client.network.defaultSecondaryDNS",
        "client.network.defaultSufixDNS"
    ]

    def __init__(self, ansible_module):
        if 'api_user' in ansible_module.params and ansible_module.params['api_user'] is not None:
            creds = (ansible_module.params['api_user'], ansible_module.params['api_pass'])
        else:
            creds = OAuth1(ansible_module.params['app_key'],
                            client_secret=ansible_module.params['app_secret'],
                            resource_owner_key=ansible_module.params['token'],
                            resource_owner_secret=ansible_module.params['token_secret'])

        self.client = Abiquo(ansible_module.params['api_url'], auth=creds, verify=ansible_module.params['verify'])
        if not ansible_module.params['verify']:
            urllib3.disable_warnings()
        self.user = None

        if 'ABQ_DEBUG' in os.environ.keys():
            self.enable_debug

    def enable_debug(self):
        '''Switches on logging of the requests module.'''
        HTTPConnection.debuglevel = 1

    def check_response(self, expected, code, dto):
        return check_response(expected, code, dto)

    def login(self):
        c, user = self.client.login.get(headers={'accept':'application/vnd.abiquo.user+json'})
        check_response(200, c, user)
        self.user = user

    def fix_link(self, dto, rel, **params):
        link = dto._extract_link(rel)
        if not link:
            raise KeyError("link with rel %s not found" % rel)
        for key in params:
            link[key] = params[key]
        return Abiquo(url=link['href'], auth=dto.auth, headers={'accept' : link['type']},
                verify=dto.verify)

    def lookup_region(self, provider, region):
        c, htypes = self.client.config.hypervisortypes.get()
        check_response(200, c, htypes)

        htype = filter(lambda x: x.name == provider, htypes)
        if len(htype) == 0:
            return None
        htype = htype[0]

        c, regions = htype.follow('regions').get()
        check_response(200, c, regions)

        region = filter(lambda x: x.name == region, regions)    
        if len(region) == 0:
            return None
        region = region[0]

        return region

    def get_datacenters(self):
        c, dcs = self.client.admin.datacenters.get(headers={'Accept': 'application/vnd.abiquo.datacenters+json'})
        check_response(200, c, dcs)
        return dcs

    def get_racks(self, dc):
        c, racks = dc.follow('racks').get()
        check_response(200, c, racks)
        return racks

    def get_machines(self, rack):
        c, machines = rack.follow('machines').get()
        check_response(200, c, machines)
        return machines

    def lookup_datacenters_and_pcrs(self, dc_names):
        datacenters = []

        # Get Datacenters
        c, dcs = self.client.admin.datacenters.get(headers={'Accept': 'application/vnd.abiquo.datacenters+json'})
        check_response(200, c, dcs)
     
        # Get PCRs
        c, pcrs = self.client.admin.publiccloudregions.get(headers={'Accept': 'application/vnd.abiquo.publiccloudregions+json'})
        check_response(200, c, pcrs)

        for dc_name in dc_names:
            dc = next((dc for dc in dcs if dc.name == dc_name), None)
            if dc is not None:
                datacenters.append(dc)
            
            pcr = next((pcr for pcr in pcrs if pcr.name == dc_name), None)
            if pcr is not None:
                datacenters.append(pcr)

        return datacenters

    def find_template(self, datacenter, template_name):
        if self.user is None:
            self.login()

        c, repo = self.get_datacenter_repo(datacenter)
        if c != 0:
            return c, repo

        c, templates = repo.follow('virtualmachinetemplates').get()
        try:
            check_response(200, c, templates)
        except Exception as ex:
            return c, ex.message

        template = filter(lambda x: x.name == template_name, templates)
        if len(template) == 0:
            return 0, None
        else:
            return 0, template[0]

    def get_datacenter_repo(self, datacenter):
        if self.user is None:
            self.login()

        c, e = self.user.follow('enterprise').get()
        try:
            check_response(200, c, e)
        except Exception as ex:
            return c, ex.message

        c, repos = e.follow('datacenterrepositories').get()
        try:
            check_response(200, c, e)
        except Exception as ex:
            return c, ex.message

        repo = filter(lambda x: x._has_link('datacenter') and x._extract_link('datacenter')['title'] == datacenter, repos)
        return 0, repo[0]

    def download_template(self, datacenter, remote_repository_url, template_name):
        if self.user is None:
            self.login()

        c, dcrepo = self.get_datacenter_repo(datacenter)
        if c != 0:
            return c, dcrepo

        c, e = self.user.follow('enterprise').get()
        try:
            check_response(200, c, e)
        except Exception as ex:
            return c, ex.message

        c, remote_repos = e.follow('appslib/templateDefinitionLists').get()
        try:
            check_response(200, c, remote_repos)
        except Exception as ex:
            return c, ex.message

        rrepo = filter(lambda x: x.url == remote_repository_url, remote_repos)
        if len(rrepo) == 0:
            return 1, "Remote repo with URL %s not found." % remote_repository_url
        rrepo = rrepo[0]

        defs = rrepo.templateDefinitions['collection']
        template_def = filter(lambda x: x['name'] == template_name, defs)
        if len(template_def) == 0:
            return 1, "Template definition with name %s not found in remote repository %s" % (template_name, remote_repository_url)
        template_def = template_def[0]

        template_link = filter(lambda x: x['rel'] == 'edit', template_def['links'])[0]
        template_link['rel'] = 'templateDefinition'

        payload = {
          'links': [ template_link ]
        }

        c, download = dcrepo.follow('virtualmachinetemplates').post(
            headers={'accept': 'application/vnd.abiquo.acceptedrequest+json', 'content-type': 'application/vnd.abiquo.virtualmachinetemplaterequest+json'},
            data=json.dumps(payload)
        )
        return c, download

    def get_network_service_types(self, dc):
        c, stypes = dc.follow('networkservicetypes').get()
        check_response(200, c, stypes)
        return stypes

    def create_machine(self, dc, rack, params):
        # Get Service Network service type:
        stypes = self.get_network_service_types(dc)
        stypesf = filter(lambda x: x.name == 'Service Network', stypes)
        if len(stypesf) == 0:
            return 1, "Could not find 'Service Network' service type."
        stype = stypesf[0]
        stypelnk = stype._extract_link('edit')
        stypelnk['rel'] = 'networkservicetype'
        
        # Discover the machine.
        disc_query_params = {
          'user': params['user'],
          'password': params['password'],
          'hypervisor': params['hyp_type'],
          'ip': params['ip'],
          'port': params['port'],
        }
        
        c, hypdisc = dc.follow('discover').get(params=disc_query_params)
        check_response(200, c, hypdisc)
        hyp = hypdisc.collection[0]
        
        # Set the network type
        for nic in hyp['networkInterfaces']['collection']:
            if nic['name'] == params['service_nic']:
                nic['links'].append(stypelnk)

        # Enable datastore
        if params['datastore_name'] is None:
            dsf = filter(lambda x: x['rootPath'] == params['datastore_root'], hyp['datastores']['collection'])
        else:
            dsf = filter(lambda x: x['name'] == params['datastore_name'], hyp['datastores']['collection'])
        ds = dsf[0]
        ds['enabled'] = True
        if params['datastore_dir'] is not None: ds['directory'] = params['datastore_dir']

        # Set credentials
        hyp['user'] = params['user']
        hyp['password'] = params['password']

        # Create the host
        c, machine = rack.follow('machines').post(
            headers={'accept':'application/vnd.abiquo.machine+json','content-type':'application/vnd.abiquo.machine+json'},
            data=json.dumps(hyp))
        return c, machine

    def getLink(self, dto_json, rel):
        links = filter(lambda x: x['rel'] == rel, dto_json['links'])
        if len(links) == 0:
            return None
        else:
            return links[0]

    def getFirstHtype(self, location):
        links = filter(lambda x: x['rel'] == "hypervisortype", location['links'])
        if len(links) == 0:
            return None
        else:
            li = links[0]
            co, ty = self.client._request("get", li['href'], headers={'accept': li['type']})
            check_response(200, co, ty)
            return ty

    def getDefaultNetworkDict(self):
        net = {}
        c, props = self.client.config.properties.get(headers={'Accept': 'application/vnd.abiquo.systemproperties+json'})
        check_response(200, c, props)

        net['name'] = (filter(lambda x: x.name == "client.network.defaultName", props)[0]).value
        net['address'] = (filter(lambda x: x.name == "client.network.defaultAddress", props)[0]).value
        net['mask'] = (filter(lambda x: x.name == "client.network.defaultNetmask", props)[0]).value
        net['gateway'] = (filter(lambda x: x.name == "client.network.defaultGateway", props)[0]).value
        net['primaryDNS'] = (filter(lambda x: x.name == "client.network.defaultPrimaryDNS", props)[0]).value
        net['secondaryDNS'] = (filter(lambda x: x.name == "client.network.defaultSecondaryDNS", props)[0]).value
        net['sufixDNS'] = (filter(lambda x: x.name == "client.network.defaultSufixDNS", props)[0]).value
        net['type'] = 'INTERNAL'

        return net

    def getMyEnterprise(self):
        c, user = self.client.login.get(headers={'accept':'application/vnd.abiquo.user+json'})
        check_response(200, c, user)
        c, enterprise = user.follow('enterprise').get()
        check_response(200, c, enterprise)

        return enterprise

    def buildScopeEntities(self, entities_jsons):
        entities = []

        for entity_json in entities_jsons:
            entity_link = self.getLink(entity_json, 'edit')

            if entity_link is None:
                # An already existing entity
                entities.append(entity_json)
            else:
                entity_type = re.search('abiquo\.(.*)\+', entity_link['type']).group(1)
                json_ent_type = "DATACENTER" if entity_type == "publiccloudregion" else entity_type.upper()

                entity = {
                    "idResource": entity_json["id"],
                    "type": json_ent_type
                }

                entities.append(entity)

        return entities

    def getDTO(self, dto_json):
        dto_url_link = self.getLink(dto_json, 'edit')
        if dto_url_link is None:
            dto_url_link = self.getLink(dto_json, 'self')

        if dto_url_link is not None:
            code, dto = self.client._request("get", dto_url_link['href'], headers={'accept': dto_url_link['type']})
            check_response(200, code, dto)
            return dto
        else:
            return None



































