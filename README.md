[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

# Additional CA for Home Assistant

Add custom CA (Certificate Authority) to Home Assistant.

ℹ️ This integration is currently under validation to be indexed by HACS.


## 1. INSTALL WITH HACS

* [Install HACS](https://hacs.xyz/docs/setup/prerequisites) if not already done.
* Go to your Home Assistant,
    * -> HACS
    * -> Integrations
    * -> Click Explore and Download repositories
    * -> Search for "Additional CA"
    * -> From the _Additional CA_ presentation page: click Download


## 2. INSTALL WITHOUT HACS

### 2.1. Docker

* Download the latest release of _Additional CA_ from Github (.zip)
    * or git clone Github repository `git clone https://github.com/Athozs/hass-additional-ca.git`
* Unzip archive (not necessary if you run git clone)
* Move `additional_ca` (under custom_components/) into `config/custom_components/` directory

### 2.2. HAOS - Home Assistant Operating System

  > ⚠️ I did not test installation on HAOS

* Go to the [Add-on store](https://my.home-assistant.io/redirect/supervisor_store/)
* Install one of the SSH add-ons (you need to enable advanced mode in your user profile to see them)
* Configure the SSH add-on you chose by following the documentation for it
* Start the SSH add-on
* Connect to the SSH add-on
* Download the latest release of _Additional CA_ from Github (.zip)

`curl -L -O https://github.com/Athozs/hass-additional-ca/archive/refs/heads/main.zip`

* Unzip archive

`unzip main.zip`

* Move `additional_ca` (under custom_components/) into `config/custom_components/` directory

`mv custom_components/additional_ca config/custom_components/`

### 2.3. Core

If you're running Home Assistant core (Python package) directly on host, you don't need _Additional CA_ integration. You should update your CAs from your host OS.


## 3. CONFIGURATION

1. Create directory `config/additional_ca` and copy your custom CAs into it.

CA files must be in PEM format. Example (this is a fake):

```text
-----BEGIN CERTIFICATE-----
ACeuur4QnujqmguSrHU3mhf+cJodzTQNqo4tde+PD1/eFdYAELu8xF+0At7xJiPY
i5RKwilyP56v+3iY2T9lw7S8TJ041VLhaIKp14MzSUzRyeoOAsJ7QADMClHKUDlH
UU2pNuo88Y6igovT3bsnwJNiEQNqymSSYhktw0taduoqjqXn06gsVioWTVDXysd5
qEx4t6sIgIcMm26YH1vJpCQEhKpc2y07gRkklBZRtMjThv4cXyyMX7uTcdT7AJBP
ueifCoV25JxXuo8d5139gwP1BAe7IBVPx2u7KN/UyOXdZmwMf/TmFGwDdCfsyHf/
ZsB2wLHozTYoAVmQ9FoU1JLgcVivqJ+vNlBhHXhlxMdN0j80R9Nz6EIglQjeK3O8
I/cFGm/B8+42hOlCId9ZdtndJcRJVji0wD0qwevCafA9jJlHv/jsE+I9Uz6cpCyh
sw+lrFdxUgqU58axqeK89FR+No4q0IIO+Ji1rJKr9nkSB0BqXozVnE1YB/KLvdIs
uYZJuqb2pKku+zzT6gUwHUTZvBiNOtXL4Nxwc/KT7WzOSd2wP10QI8DKg4vfiNDs
HWmB1c4Kji6gOgA5uSUzaGmq/v4VncK5Ur+n9LbfnfLc28J5ft/GotinMyDk3iar
F10YlqcOmeX1uFmKbdi/XorGlkCoMF3TDx8rmp9DBiB/
-----END CERTIFICATE-----
```

Optionally, you could group CAs into folders.

Directories structure example:

```text
.
├── compose.yml
├── config/
│   ├── additional_ca/
│   │   ├── my_ca.crt
│   │   └── some-super-ca/
|   |       ├── ca2.pem
│   │       └── ca3.crt
│   ├── blueprints/
│   │   └── ...
│   ├── configuration.yaml
│   ├── custom_components/
│   │   └── additional_ca/
│   │       ├── __init__.py
│   │       ├── const.py
│   │       └── manifest.json
│   ├── ...
...
```

2. Enable _Additional CA_ integration in `configuration.yaml` and set custom CAs:

Model:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  <string>: <CA filename or CA relative path as string>
  <string>: <CA filename or CA relative path as string>
  <string>: <CA filename or CA relative path as string>
  # ...: ...
```

Example:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  my_awesome_ca: my_ca.crt  # a cert file
  another_super_ca: some-super-ca/ca2.pem  # a folder + a cert file
  again_another_super_ca: some-super-ca/ca3.crt  # a folder + a cert file
# ...
```

3. Optionally, set environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`

Example using Docker Compose:

```yaml
# compose.yml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    hostname: home-assistant
    image: homeassistant/home-assistant:2023.5.2
    volumes:
      - ./config:/config
    environment:
      - TZ=Europe/Paris
      - REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    restart: unless-stopped
    network_mode: host
```

4. Restart Home Assistant
5. Check the logs, look for pattern `additional_ca` (there is not UI for _Additional CA_)


## 4. HOW DOES _Additional CA_ WORK UNDER THE HOOD ?

When enabled, _Additional CA_ integration looks for custom Certificates Authorities files (CAs) in `config/additional_ca` directory.

It loads custom CAs only at Home Assistant startup.

It copies custom CAs to `/usr/local/share/ca-certificates/` directory inside container and uses `update-ca-certificates` command line.

For now, _Additional CA_ won't be visible in Home Assistant integrations dashboard, there is not UI component for _Additional CA_ integration. This may be possible in future release.


## 5. `REQUESTS_CA_BUNDLE` ENVIRONMENT VARIABLE

This is optional.

Some of Home Assistant integrations may use the famous _Requests_ Python package.

If some of your installed Home Assistant integrations (using _Requests_ under the hood) need to access remote servers using your custom CA, then you will have to set environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`, [so those integrations are aware of your custom CA](https://requests.readthedocs.io/en/latest/user/advanced/#ca-certificates).

If your HA integrations does not use _Requests_ Python package, then no need to set `REQUESTS_CA_BUNDLE`.

__How do I know if HA integrations use _Requests_ Python package ?__

Read the Python code of those integrations and seek for `requests` package.

Anyway, setting environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` __should not__ break your Home Assistant server.


## 6. HOW TO REMOVE CUSTOM CA ?

Remove or comment entries under `additional_ca:` in `configuration.yaml`:

```yaml
---
default_config:
additional_ca:
  # my_awesome_ca: my_ca.crt
  # another_super_ca: some-super-ca/ca2.pem
  # again_another_super_ca: some-super-ca/ca3.crt
# ...
```

`additional_ca:` need to be enabled in `configuration.yaml` to remove CA files on next restart of Home Assistant.

Optionally remove them from `config/additional_ca/` directory.


## 7. TROUBLESHOOTING

Some tips to clean your system CA in case of failure:

- Manually remove custom CA files from `/usr/local/share/ca-certificates/` directory inside HA container
- Then update manually system CA running command `update-ca-certificates` inside HA container
