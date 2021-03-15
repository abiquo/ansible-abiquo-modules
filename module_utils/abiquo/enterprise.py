import json

from common import AbiquoCommon
from abiquo.client import check_response


def list(module):
    common = AbiquoCommon(module)
    api = common.client

    code, enterprises = api.admin.enterprises.get(
        headers={'Accept': 'application/vnd.abiquo.enterprises+json'})
    check_response(200, code, enterprises)

    all_enterprises = []
    for enterprise in enterprises:
        all_enterprises.append(enterprise)

    return all_enterprises


def find_by_link(module, link):
    common = AbiquoCommon(module)
    api = common.client

    code, enterprises = api.admin.enterprises.get(headers={'Accept': 'application/vnd.abiquo.enterprises+json'},
                                                  params={'has': link['title']})
    check_response(200, code, enterprises)

    for enterprise in enterprises:
        enterprise_link = enterprise._extract_link('edit')
        if enterprise_link['href'] == link['href']:
            return enterprise

    return None


def get_repo_for_dc(enterprise, datacenter):
    code, repos = enterprise.follow('datacenterrepositories').get()
    check_response(200, code, repos)

    datacenter_link = datacenter._extract_link('edit')

    for repo in repos:
        repo_dc_pcr_link = None
        if repo._has_link('datacenter'):
            repo_dc_pcr_link = repo._extract_link('datacenter')
        else:
            repo_dc_pcr_link = repo._extract_link('publiccloudregion')

        if repo_dc_pcr_link['href'] == datacenter_link['href']:
            return repo

    return None
