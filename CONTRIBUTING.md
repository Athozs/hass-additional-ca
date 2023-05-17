# Development environment setup

## Requirements

- Python (version 3.10 currently)
- Pip
- Docker and Docker Compose
- rsync


## Setup

After git clone,

```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt
```


## Test

```shell
mkdir -p config
bash scripts/run-compose.sh
```
