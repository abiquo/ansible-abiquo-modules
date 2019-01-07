import json

from common import AbiquoCommon
from abiquo.client import check_response
import datacenter

def lookup_result(task):
    code, template = task.follow('result').get()
    check_response(200, code, template)
    return template

def delete(template):
    code, resp = template.delete()
    check_response(204, code, resp)

def update(template, module):
    if module.params.get('attribs') is not None:
        for k, v in module.params.get('attribs').iteritems():
            setattr(template, k, v)
            code, template = template.put()
            check_response(200, code, template)
    
    return template

def download(module, datacenter_name, remote_repository_url, template_name):
    common = AbiquoCommon(module)
    common.login()

    dcrepo = datacenter.get_datacenter_repo(datacenter_name, module)
    if dcrepo is None:
        raise Exception('DC repo not found for datacenter %s' % datacenter_name)

    code, enterprise = common.user.follow('enterprise').get()
    check_response(200, code, enterprise)
    
    code, remote_repos = enterprise.follow('appslib/templateDefinitionLists').get()
    check_response(200, code, remote_repos)
    
    rrepo = filter(lambda x: x.url == remote_repository_url, remote_repos)
    if len(rrepo) == 0:
        raise Exception("Remote repo with URL %s not found." % remote_repository_url)
    rrepo = rrepo[0]

    defs = rrepo.templateDefinitions['collection']
    template_def = filter(lambda x: x['name'] == template_name, defs)
    if len(template_def) == 0:
        raise Exception("Template definition with name %s not found in remote repository %s" % (template_name, remote_repository_url))
    template_def = template_def[0]

    template_link = filter(lambda x: x['rel'] == 'edit', template_def['links'])[0]
    template_link['rel'] = 'templateDefinition'

    payload = {
      'links': [ template_link ]
    }

    code, download_task = dcrepo.follow('virtualmachinetemplates').post(
        headers={'accept': 'application/vnd.abiquo.acceptedrequest+json', 'content-type': 'application/vnd.abiquo.virtualmachinetemplaterequest+json'},
        data=json.dumps(payload)
    )
    check_response(202, code, download_task)
    return download_task
