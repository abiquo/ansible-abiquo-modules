# Demonstration: how to deploy a VM in Abiquo using ansible
This Repository creates Vapps and VMs into an existing VDC. 

## Pre-requisites
It is recommended to boot a virtual machine to test this, so you have to set your environment up before proceeding.

1. Install the requirements.txt and requirements.yml

    ```bash
    sudo apt install --assume-yes ansible vim python3 python3-pip git
    ansible-galaxy install -r requirements.yml
    sudo pip3 install -r requirements.txt
    ```

## Prepare the environment
### Create some resources in your Abiquo UI:

1. Make sure that your Abiquo environment has a working VDC and some templates.

### Customize the deploy-and-configure-vm.yml file and adapt it to your environemnt
Edit these variables from the `deploy-and-configure-vm.yml` file:

```yaml
vapp_name: "abiquo-ansible-demo"
vdc_id: "Your VDC ID"
template_name: "YourTemplateName"
```

## Launch the application
Create a file named `vault-password.txt` and make it contain your ansible vault's password (see [credentials for the entry "abiquo-devops-features-demonstration - ansible vault password"](https://vault.bitwarden.com/#/vault)).

```bash
ansible-playbook deploy-and-configure-vm.yml -vvv
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
