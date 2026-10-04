# Development environment setup

## Requirements

- Python (latest stable)
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


## Create a new GitHub release

Use the release script `bump-version.sh` with a bare semver version (no `v` prefix). It updates the manifest, commits and pushes the version tag, which triggers the GitHub release workflow.

Example:

```shell
bash scripts/bump-version.sh 0.6.2
```
