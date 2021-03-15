import json

from common import AbiquoCommon
from abiquo.client import check_response
from ansible.module_utils.abiquo import currency as currencies_module


def list(module):
    common = AbiquoCommon(module)
    api = common.client

    code, pricing_templates = api.config.pricingtemplates.get(
        headers={'accept': 'application/vnd.abiquo.pricingtemplates+json'})
    check_response(200, code, pricing_templates)

    all_pricing_templates = []
    for ptemplate in pricing_templates:
        all_pricing_templates.append(ptemplate)

    return all_pricing_templates


def find(module):
    template_name = module.params.get('name')
    pricing_templates = list(module)
    filtered_templates = filter(lambda x: x.name == template_name, pricing_templates)
    if len(filtered_templates) == 0:
        return None
    else:
        return filtered_templates[0]


def create(module):
    common = AbiquoCommon(module)
    api = common.client

    all_currencies = currencies_module.list(module)
    module_currency_link = module.params.get('currency')
    currencies = filter(lambda x: x._extract_link(
        'edit')['href'] == module_currency_link['href'], all_currencies)
    if len(currencies) == 0:
        raise ValueError(
            "Currency sith symbol '%s' cannot be found." %
            module.params.get('currency'))
    currency_lnk = currencies[0]._extract_link('edit')
    currency_lnk['rel'] = 'currency'

    pricing_template_dict = {
        "name": module.params.get('name'),
        "description": module.params.get('description'),
        "standingChargePeriod": module.params.get('standingChargePeriod'),
        "showMinimumCharge": module.params.get('showMinimumCharge'),
        "chargingPeriod": module.params.get('chargingPeriod'),
        "minimumChargePeriod": module.params.get('minimumChargePeriod'),
        "showChangesBefore": module.params.get('showChangesBefore'),
        "minimumCharge": module.params.get('minimumCharge'),
        "defaultTemplate": module.params.get('defaultTemplate'),
        "deployMessage": module.params.get('deployMessage'),
        "links": [currency_lnk]
    }

    code, cur = api.config.pricingtemplates.post(
        headers={'accept': 'application/vnd.abiquo.pricingtemplate+json',
                 'content-Type': 'application/vnd.abiquo.pricingtemplate+json'},
        data=json.dumps(pricing_template_dict)
    )
    check_response(201, code, cur)

    return cur


def delete(template):
    code, resp = template.delete()
    check_response(204, code, resp)
