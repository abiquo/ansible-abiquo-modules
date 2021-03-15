import json

from common import AbiquoCommon
from abiquo.client import check_response


def list(module):
    common = AbiquoCommon(module)
    api = common.client

    code, currencies = api.config.currencies.get(
        headers={'accept': 'application/vnd.abiquo.currencies+json'})
    check_response(200, code, currencies)

    all_currencies = []
    for currency in currencies:
        all_currencies.append(currency)

    return all_currencies
