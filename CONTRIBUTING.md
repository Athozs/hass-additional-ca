# Development environment setup

## Requirements

- Python (version 3.11 currently)
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


## Run

```shell
bash scripts/run-compose.sh
```


## Manual test with HTTPS

- Add your private CA file into `config/additional_ca/`

```shell
mkdir -p config/additional_ca
cp ca.crt config/additional_ca/
```

- Add the following config to `configuration.yaml`:

```yaml
logger:
  default: info

additional_ca:
  my_ca: ca.crt

rest_command:
  additional_ca_test:
    url: "https://example.com/"  # <- use your own url here
    method: get
    verify_ssl: true
    timeout: 30

```

- Then call service `RESTful Command: additional_ca_test` from Developer tools panel. Starting from Home Assistant version 2024.2.x, you should see `status: 200` in response to confirm success.

-  If TLS/SSL does not work, you will see error details in Home Assistant logs:

```text
[homeassistant.components.rest_command] Client error. Url: https://example.com/. Error: Cannot connect to host example.com ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')]
```
