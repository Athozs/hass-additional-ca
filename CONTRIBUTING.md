# Development environment setup

## Requirements

- Python (version 3.13 currently)
- Pip
- Docker and Docker Compose


## Setup

After git clone,

```shell
python3 -m venv venv
source venv/bin/activate
pip install -U -r requirements_dev.txt
```


## Run Home Assistant with Docker Compose

```shell
bash scripts/run-compose.sh
```


## Run pytest

```shell
pip install -U -r requirements_test.txt
pytest test/unit/ -v
```
