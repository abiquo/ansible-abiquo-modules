import json
from abiquo.client import check_response


def create_tags(vm, module):
    tags_data = module.params.get('tags')

    code, tags = vm.follow('tags').put(
        headers={
            'accept': 'application/vnd.abiquo.asynctask+json',
            'content-Type': 'application/vnd.abiquo.tags+json'
        },
        data=json.dumps(tags_data)
    )
    check_response(200, code, tags)
    return tags
