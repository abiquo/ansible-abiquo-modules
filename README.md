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
