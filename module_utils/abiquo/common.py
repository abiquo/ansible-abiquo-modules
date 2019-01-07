from abiquo.client import Abiquo
from abiquo.client import check_response
from requests_oauthlib import OAuth1
from ansible.module_utils.basic import AnsibleModule
import json, urllib3, os, re, time

try:
    from http.client import HTTPConnection # py3
except ImportError:
    from httplib import HTTPConnection # py2

def abiquo_argument_spec():
    return dict(
        api_url      = dict(default=None, required=False),
        verify       = dict(default=True, required=False, type='bool'),
        api_user     = dict(default=None, required=False),
        api_pass     = dict(default=None, required=False, no_log=True),
        app_key      = dict(default=None, required=False),
        app_secret   = dict(default=None, required=False),
        token        = dict(default=None, required=False, no_log=True),
        token_secret = dict(default=None, required=False, no_log=True),
        max_attempts = dict(default=30, required=False, type='int'),
        retry_delay  = dict(default=10, required=False, type='int')
    )

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
        if os.environ.get('ABIQUO_API_URL') is not None:
            ansible_module.params['api_url'] = os.environ.get('ABIQUO_API_URL')
        if os.environ.get('ABIQUO_API_USERNAME') is not None:
            ansible_module.params['api_user'] = os.environ.get('ABIQUO_API_USERNAME')
        if os.environ.get('ABIQUO_API_PASSWORD') is not None:
            ansible_module.params['api_pass'] = os.environ.get('ABIQUO_API_PASSWORD')
        if os.environ.get('ABIQUO_API_APP_KEY') is not None:
            ansible_module.params['app_key'] = os.environ.get('ABIQUO_API_APP_KEY')
        if os.environ.get('ABIQUO_API_APP_SECRET') is not None:
            ansible_module.params['app_secret'] = os.environ.get('ABIQUO_API_APP_SECRET')
        if os.environ.get('ABIQUO_API_TOKEN') is not None:
            ansible_module.params['token'] = os.environ.get('ABIQUO_API_TOKEN')
        if os.environ.get('ABIQUO_API_TOKEN_SECRET') is not None:
            ansible_module.params['token_secret'] = os.environ.get('ABIQUO_API_TOKEN_SECRET')

        if ansible_module.params.get('api_url') is None:
            raise ValueError('Abiquo API URL is missing!!')

        if ansible_module.params.get('api_user') is not None:
            creds = (ansible_module.params.get('api_user'), ansible_module.params.get('api_pass'))
        elif ansible_module.params.get('app_key') is not None:
            creds = OAuth1(ansible_module.params.get('app_key'),
                            client_secret=ansible_module.params.get('app_secret'),
                            resource_owner_key=ansible_module.params.get('token'),
                            resource_owner_secret=ansible_module.params.get('token_secret'))
        else:
            raise ValueError('Either basic auth or OAuth creds are required.')

        self.client = Abiquo(ansible_module.params.get('api_url'), auth=creds, verify=ansible_module.params.get('verify'))
        if not ansible_module.params.get('verify'):
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

    def track_task(self, task, attempts, delay):
        if task._has_link('status'):
            # Not a task, but the accepted request
            code, task = task.follow('status').get()
            check_response(200, code, task)

        for i in range(attempts):
            task_link = task._extract_link('self')
            task_link['type'] = "application/vnd.abiquo.task+json"
            # code, task = task.refresh(params=None, headers={'accept':'application/vnd.abiquo.task+json'})
            # check_response(200, code, task)
            task = self.get_dto_from_link(task_link)

            if task.state.startswith('FINISHED'):
                return task
            else:
                time.sleep(delay)
        raise ValueError('Exceeded %s attempts tracking task of type %s for %s' % (attempts, task.type, task.ownerId))

    def login(self):
        code, user = self.client.login.get(headers={'accept':'application/vnd.abiquo.user+json'})
        check_response(200, code, user)
        self.user = user
