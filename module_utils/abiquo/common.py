from abiquo.client import Abiquo
from abiquo.client import check_response
from requests_oauthlib import OAuth1
from ansible.module_utils.basic import AnsibleModule
import json, urllib3, os, re, time, copy

try:
    from http.client import HTTPConnection # py3
except ImportError:
    from httplib import HTTPConnection # py2

def abiquo_argument_spec():
    return dict(
        abiquo_api_url      = dict(default=None, required=False),
        abiquo_verify       = dict(default=True, required=False, type='bool'),
        abiquo_api_user     = dict(default=None, required=False),
        abiquo_api_pass     = dict(default=None, required=False, no_log=True),
        abiquo_app_key      = dict(default=None, required=False),
        abiquo_app_secret   = dict(default=None, required=False),
        abiquo_token        = dict(default=None, required=False, no_log=True),
        abiquo_token_secret = dict(default=None, required=False, no_log=True),
        abiquo_max_attempts = dict(default=30, required=False, type='int'),
        abiquo_retry_delay  = dict(default=10, required=False, type='int'),
        links               = dict(default=None, required=False, type=dict)
    )

def abiquo_updatable_arguments(args):
    updatable_args = []
    for arg in args:
        if 'abiquo_updatable' in arg and arg['abiquo_updatable']:
            updatable_args.append(arg)

    return updatable_args

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
        api_url = ansible_module.params.get('abiquo_api_url')
        verify = ansible_module.params.get('abiquo_verify')
        api_user = ansible_module.params.get('abiquo_api_user')
        api_pass = ansible_module.params.get('abiquo_api_pass')
        app_key = ansible_module.params.get('abiquo_app_key')
        app_secret = ansible_module.params.get('abiquo_app_secret')
        token = ansible_module.params.get('abiquo_token')
        token_secret = ansible_module.params.get('abiquo_token_secret')

        # API URL
        if not api_url:
            if os.environ.get('ABIQUO_API_URL') is not None and os.environ.get('ABIQUO_API_URL') != "":
                api_url = os.environ.get('ABIQUO_API_URL')
            else:
                raise ValueError('Abiquo API URL is missing!!')

        if os.environ.get('ABIQUO_API_INSECURE') is not None:
            verify = False

        # Basic auth
        if not api_user:
            if os.environ.get('ABIQUO_API_USERNAME') is not None and os.environ.get('ABIQUO_API_USERNAME') != "":
                api_user = os.environ.get('ABIQUO_API_USERNAME')
        if not api_pass:
            if os.environ.get('ABIQUO_API_PASSWORD') is not None and os.environ.get('ABIQUO_API_PASSWORD') != "":
                api_pass = os.environ.get('ABIQUO_API_PASSWORD')

        # OAuth1
        if not app_key:
            if os.environ.get('ABIQUO_API_APP_KEY') is not None and os.environ.get('ABIQUO_API_APP_KEY') != "":
                app_key = os.environ.get('ABIQUO_API_APP_KEY')
        if not app_secret:
            if os.environ.get('ABIQUO_API_APP_SECRET') is not None and os.environ.get('ABIQUO_API_APP_SECRET') != "":
                app_secret = os.environ.get('ABIQUO_API_APP_SECRET')
        if not token:
            if os.environ.get('ABIQUO_API_TOKEN') is not None and os.environ.get('ABIQUO_API_TOKEN') != "":
                token = os.environ.get('ABIQUO_API_TOKEN')
        if not token_secret:
            if os.environ.get('ABIQUO_API_TOKEN_SECRET') is not None and os.environ.get('ABIQUO_API_TOKEN_SECRET') != "":
                token_secret = os.environ.get('ABIQUO_API_TOKEN_SECRET')

        if api_user is not None:
            creds = (api_user, api_pass)
        elif app_key is not None:
            creds = OAuth1(app_key,
                        client_secret=app_secret,
                        resource_owner_key=token,
                        resource_owner_secret=token_secret)
        else:
            raise ValueError('Either basic auth or OAuth creds are required.')

        self.client = Abiquo(api_url, auth=creds, verify=verify)
        if not verify:
            urllib3.disable_warnings()
        self.user = None

        if os.environ.get('ABQ_DEBUG'):
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

    def get_dto_from_link(self, link_json):
        code, dto = self.client._request("get", link_json['href'], headers={'accept': link_json['type']})
        check_response(200, code, dto)
        return dto

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

    def getLink(self, dto_json, rel):
        links = filter(lambda x: x['rel'] == rel, dto_json['links'])
        if len(links) == 0:
            return None
        else:
            return links[0]

    def track_async_task(self, async_task, attempts, delay):
        for i in range(attempts):
            code, async_task = async_task.refresh()
            check_response(200, code, async_task)

            if async_task.finished:
                return async_task
            else:
                time.sleep(delay)
        raise ValueError('Exceeded %s attempts tracking async task of type %s for %s' % (attempts, task.type, task.ownerId))

    def async_task_status_ok(self, async_task):
        jobs = async_task.jobs
        for job in jobs['collection']:
            if job['status'] not in ['FinishedSuccessfully', 'Completed']:
                return False
        return True

    def track_task(self, task, attempts, delay):
        if task._has_link('status'):
            # Not a task, but the accepted request
            code, task = task.follow('status').get()
            check_response(200, code, task)

        for i in range(attempts):
            task_link = task._extract_link('self')
            task_link['type'] = "application/vnd.abiquo.task+json"

            task = self.get_dto_from_link(task_link)

            if task.state.startswith('FINISHED'):
                return task
            else:
                time.sleep(delay)
        raise ValueError('Exceeded %s attempts tracking async task' % attempts)

    def login(self):
        code, user = self.client.login.get(headers={'accept':'application/vnd.abiquo.user+json'})
        check_response(200, code, user)
        self.user = user

    def link_from_list(self, rel, links):
        return next((link for link in links if link['rel'] == rel), None)

    def changes_required(self, source, dest):
        source_copy = copy.deepcopy(source)
        dest_copy = copy.deepcopy(dest)
        del dest_copy['state']

        links_source = source_copy.pop('links')
        links_dest = dest_copy.pop('links', None)

        for k, v in dest_copy.items():
            if k not in source_copy or source_copy[k] != v:
                return True

        if links_dest is not None:
            for link in links_dest:
                src_link = self.link_from_list(link['rel'], links_source)
                if src_link is None and 'remove' in link:
                    continue
                if src_link is None or not src_link.__eq__(link):
                    return True

        return False

    def build_json(self, module):
        dto_dict = {}
        dto_dict['links'] = []

        dto = copy.deepcopy(module.params)
        links = dto.pop('links')

        for k, v in dto.items():
            if not k.startswith('abiquo_'):
                dto_dict[k] = v

        if links is not None:
            for link_rel, link in links.items():
                link['rel'] = link_rel
                dto_dict['links'].append(link)

        return dto_dict

    def update_dto(self, abiquo_dto, module):
        dto = copy.deepcopy(module.params)
        links = dto.pop('links')

        for k, v in dto.items():
            if not k.startswith('abiquo_'):
                abiquo_dto.__setattr__(k, v)

        if links is not None:
            for link_rel, link in links.items():
                link['rel'] = link_rel
                if abiquo_dto._has_link(link_rel):
                    abiquo_dto.links.remove(abiquo_dto._extract_link(link_rel))
                if not 'remove' in link:
                    abiquo_dto.links.append(link)

        code, updated_dto = abiquo_dto.put()
        self.check_response(200, code, updated_dto)
        return updated_dto

    def getDefaultNetworkDict(self):
        net = {}
        code, props = self.client.config.properties.get(headers={'Accept': 'application/vnd.abiquo.systemproperties+json'})
        check_response(200, code, props)

        net['name'] = (filter(lambda x: x.name == "client.network.defaultName", props)[0]).value
        net['address'] = (filter(lambda x: x.name == "client.network.defaultAddress", props)[0]).value
        net['mask'] = (filter(lambda x: x.name == "client.network.defaultNetmask", props)[0]).value
        net['gateway'] = (filter(lambda x: x.name == "client.network.defaultGateway", props)[0]).value
        net['primaryDNS'] = (filter(lambda x: x.name == "client.network.defaultPrimaryDNS", props)[0]).value
        net['secondaryDNS'] = (filter(lambda x: x.name == "client.network.defaultSecondaryDNS", props)[0]).value
        net['sufixDNS'] = (filter(lambda x: x.name == "client.network.defaultSufixDNS", props)[0]).value
        net['type'] = 'INTERNAL'

        return net
