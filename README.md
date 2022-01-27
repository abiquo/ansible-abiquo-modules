# Ansible Abiquo Modules
Ansible Abiquo Modules are ansible roles that make it possible to perform operations against abiquo's environment through their API using ansible.

## Installation

Use the [requirements.yml standard file](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html#installing-roles-and-collections-from-the-same-requirements-yml-file) to install this module.
For example:

```
- src: git+git@github.com:abiquo/ansible-abiquo-modules.git
    version: master
```
After that, run: 
```
$ ansible-galaxy install -r requirements.yml
```

## Usage
You can use this module directly from an ansible task or you can use it to create specific roles.
For example, a new deploy-vm role can be created on a specific project. The tasks/main.yml could be:

```
---
- name: import role
  import_role: 
    name: ansible-abiquo-modules
  
- name: Gather VDC
  abiquo_vdc_facts:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    id: "{{ env_vdc }}" #this is the VDC ID
  register: evdc

- fail:
    msg: "ERROR: no information returned for the VDC named '{{ env_vdc }}'"
  when: evdc.vdcs is not defined or (evdc.vdcs | length <= 0)

- name: "Create vApp '{{ vapp_name }}'"
  abiquo_vapp:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    name: "{{ vapp_name }}"
    vdc: "{{ evdc.vdcs[0].vdc_link }}"
    iconUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Ansible_logo.svg/1200px-Ansible_logo.svg.png"
  register: evapp

- name: "Locate template '{{ env_vm_template }}'"
  abiquo_vdc_template_facts:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    vdc: "{{ evdc.vdcs[0] }}"
    params:
      has: "{{ env_vm_template }}"
  register: etpl

- set_fact:
    template: "{{ etpl.templates | selectattr('name', 'eq', env_vm_template) | list | first }}"

- name: "Locate HW Profile '{{ env_vm_hwprofile }}'"
  abiquo_vdc_hwprofile_facts:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    vdc: "{{ evdc.vdcs[0] }}"
    params:
      has: "{{ env_vm_hwprofile }}"
  register: ehw

- set_fact:
    hwprofile_links: "{{ ehw.hwprofiles | selectattr('name', 'eq', env_vm_hwprofile) | map(attribute='hwprofile_link') | list }}"

- set_fact:
    standard_tags:
      type: "{{ vm_label }}"
      created_date: "{{ ansible_date_time.date }}"
      created_time: "{{ ansible_date_time.time }}"

- name: "Create {{ vm_label }} VM"
  no_log: true
  abiquo_vm:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    template: "{{ template.template_link }}"
    vapp: "{{ evapp.vapp_link }}"
    hardwareprofile: "{{ hwprofile_links | first }}"
    label: "{{ vm_label }}"
    tags: "{{ vm_tags | default({}) | combine(standard_tags) }}"
  register: VM
 
- name: set vm link
  set_fact:
    vm_link: "{{ VM.vm.links | selectattr('rel', 'eq', 'edit') | list}}"

- name: "Deploy {{ vm_label }} VM"
  abiquo_vm:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    abiquo_max_attempts: 300
    vapp: "{{ evapp.vapp_link }}"
    label: "{{ vm_label }}"
    template: "{{ template.template_link }}"
    state: deploy
  #register: edvms

- name: Wait for VM sync to get the db IP
  abiquo_vm:
    abiquo_api_url: "{{ api_url }}"
    abiquo_api_user: "{{ api_user }}"
    abiquo_api_pass: "{{ api_pass }}"
    abiquo_verify: "{{ verify_ssl }}"
    template: "{{ template.template_link }}"
    vapp: "{{ evapp.vapp_link }}"
    hardwareprofile: "{{ hwprofile_links | first }}"
    label: "{{ vm_label }}"
  register: VM
  until: "{{ VM.vm.links | selectattr('rel', 'eq', 'nic0') | list | length > 0 }}"
  retries: 30
  delay: 10

- name: remove known_hosts file
  file:
    path: /root/.ssh/known_hosts
    state: absent
  delegate_to: localhost
```
Of course, you could be able to run this new role through the following task (adding the corresponding variables):
```
---
- name: Deploy VM from template
  hosts: localhost

  tasks:
    - name: create vm
      include_role:
        name: abiquo-deploy-vm
      vars: 
        api_url: "{{ abiquo_api_endpoint }}"
        api_user: "{{ abiquo_api_username }}"
        api_pass: "{{ abiquo_api_password }}"
        verify_ssl: false
        vapp_name: "{{ abiquo_vapp }}"
        env_vdc: "{{ abiquo_id_vdc }}"
        env_vm_template: "{{ template_name }}"
        env_vm_hwprofile: "{{ abiquo_hwprofile }}"
        vm_label: "{{ vm_name }}"
        vm_tags:
          role: "{{ vm_name }}"
          app: "{{ app }}"
```

## Contributing

Pull requests are welcome. Not all modules have been tested lately, so feel free to improve anything or to ask any doubts. 


# Development

## Prepare development environment

Install virtual env package:
```bash
sudo apt install -y python3-venv
```

Create virtual env
```bash
python3 -m venv ansible-abiquo-module
```

Activate virtual env
```bash
source ansible-abiquo-module/bin/activate
```


## Before commiting

Install autopep8 to fix coding style issues automatically.
```bash
$ pip install --upgrade autopep8
```

Please, run autopep8 to fix all CS issues:
```bash
$ make cs-fix
```
