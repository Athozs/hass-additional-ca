[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
<!-- ![Total downloads](https://img.shields.io/github/downloads/athozs/hass-additional-ca/total) -->
<!--
[![Release version](https://img.shields.io/github/v/release/Athozs/hass-additional-ca?color=brightgreen&label=Download&style=for-the-badge)](https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip "Download")
-->

<p align="center">
  <img src="img/hass-additional-ca-icon.png" />
</p>

# Additional CA for Home Assistant

_Additional CA_ integration for Home Assistant loads automatically private Certificate Authority or self-signed certificate into Home Assistant in order to access 3rd-party service with TLS/SSL, even after Home Assistant is upgraded.


## 📘 What to understand meaning private Certificate Authority (CA) ?

* In case you manage your own CA, or you trust a CA, it gives you a kind of `ca.crt` file (or equivalent), that could be named shortly a personal / own / private / custom CA.

* In case you generate a self-signed TLS/SSL certificate, it gives you a `.crt` file (or equivalent), that could be an equivalent of a personal / own / private / custom trusted CA.

📒 This documentation uses 'private CA' or 'self-signed cert' alternatively for the same purpose.


## 📘 What are use-cases with this integration ?

Scenario: you want to import Certificate file into Home Assistant OS (HAOS) trust store or Home Assistant Docker container trust store, in order to access 3rd-party service with TLS/SSL:

* Some of your installed integrations in Home Assistant need to access devices or third-party services with TLS/SSL (HTTPS, etc), and you got a `ca.crt` (or equivalent) from the service provider, ➡ you can load it with _Additional CA_ integration.
* You generated a self-signed TLS/SSL certificate for your own service (personal HTTPS Web server, SMTP, LDAP, etc) that you want to be trusted by Home Assistant, ➡ you can load it with _Additional CA_ integration.

![](img/hass-additional-ca.png)


## 📘 Quick Setup (TL;DR)

1. [Install HACS](https://www.hacs.xyz/docs/use/)
2. Install _Additional CA_ integration via HACS or manually without HACS, full docs here-under
3. Copy private CA to config folder:

```shell
mkdir -p config/additional_ca
cp my_ca.crt config/additional_ca/
```

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  my_private_ca: my_ca.crt
# ...
```

4. Export environment variable if running Home Assistant with Docker (no need in case of installation type Home Assistant OS (HAOS)):

```yaml
# compose.yml
version: '3'
services:
  homeassistant:
    # ...
    environment:
      - REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

5. Restart Home Assistant
6. Done!


___

__Table of contents__

- [Additional CA for Home Assistant](#additional-ca-for-home-assistant)
  - [📘 What to understand meaning private Certificate Authority (CA) ?](#-what-to-understand-meaning-private-certificate-authority-ca-)
  - [📘 What are use-cases with this integration ?](#-what-are-use-cases-with-this-integration-)
  - [📘 Quick Setup (TL;DR)](#-quick-setup-tldr)
  - [1. INSTALL WITH HACS](#1-install-with-hacs)
  - [2. INSTALL WITHOUT HACS](#2-install-without-hacs)
    - [2.1. Docker](#21-docker)
      - [2.1.1. Install using `git`:](#211-install-using-git)
      - [2.1.2. Install using `wget`:](#212-install-using-wget)
    - [2.2. HAOS - Home Assistant Operating System](#22-haos---home-assistant-operating-system)
    - [2.3. Core](#23-core)
  - [3. CONFIGURATION](#3-configuration)
  - [4. UPGRADE](#4-upgrade)
    - [4.1. Home Assistant](#41-home-assistant)
    - [4.2. Additional CA](#42-additional-ca)
  - [5. HOW DOES _Additional CA_ WORK UNDER THE HOOD ?](#5-how-does-additional-ca-work-under-the-hood-)
    - [5.1. Docker](#51-docker)
    - [5.2. HAOS - Home Assistant Operating System](#52-haos---home-assistant-operating-system)
  - [6. SET `REQUESTS_CA_BUNDLE` ENVIRONMENT VARIABLE](#6-set-requests_ca_bundle-environment-variable)
    - [6.1. Docker and Core](#61-docker-and-core)
    - [6.2. HAOS - Home Assistant Operating System](#62-haos---home-assistant-operating-system)
  - [7. HOW TO TEST YOUR CA WITH HTTPS](#7-how-to-test-your-ca-with-https)
    - [7.1. Test with RESTful Command action](#71-test-with-restful-command-action)
    - [7.2. Test with `curl`](#72-test-with-curl)
      - [7.2.1. Docker](#721-docker)
      - [7.2.2. HAOS - Home Assistant Operating System](#722-haos---home-assistant-operating-system)
  - [8. HOW TO REMOVE A PRIVATE CA ?](#8-how-to-remove-a-private-ca-)
  - [9. UNINSTALL](#9-uninstall)
  - [10. TROUBLESHOOTING](#10-troubleshooting)
    - [10.1. General troubleshooting](#101-general-troubleshooting)
    - [10.2. Reset CA trust store of Home Assistant](#102-reset-ca-trust-store-of-home-assistant)
      - [10.2.1. Docker](#1021-docker)
      - [10.2.2. HAOS - Home Assistant Operating System](#1022-haos---home-assistant-operating-system)
    - [10.3. Tips](#103-tips)
  - [11. KNOWN ISSUES](#11-known-issues)


## 1. INSTALL WITH HACS

To install _Additional CA_ integration with HACS:

* [Install HACS](https://hacs.xyz/docs/use/) if not already done.
* Then, go to your Home Assistant,
    * -> HACS
    * -> Search for "Additional CA"
    * -> Click the three-dots menu in line with _Additional CA_, then click _Download_

<!--
If _Additional CA_ integration is not available from HACS interface, install _Additional CA_ by adding this Github repository to HACS custom repositories:

* [Install HACS](https://hacs.xyz/docs/use/) if not already done.
* Then, go to your Home Assistant,
    * -> HACS
    * -> Click the three-dots menu in top-right corner
    * -> Custom repositories
    * -> Fill in
      - Repository: https://github.com/Athozs/hass-additional-ca.git
      - Type: Integration
    * -> Click Add

![](img/hacs-custom-repo.png) ![](img/hacs-repo-box.png)
-->


## 2. INSTALL WITHOUT HACS

### 2.1. Docker

To install _Additional CA_ integration without HACS, if you're running Home Assistant with Docker, you can use `git` or `wget`.

#### 2.1.1. Install using `git`:

Download and install using `git`:

```shell
# move to your Home Assistant directory containing the 'config' folder
cd /path/to/home-assistant
# git clone Addition CA integration
git clone https://github.com/Athozs/hass-additional-ca.git
# copy additional_ca integration to Home Assistant custom components
mkdir -p config/custom_components
cp -r hass-additional-ca/custom_components/additional_ca config/custom_components/
# Installation done, now see Configuration section (README.md)
```

#### 2.1.2. Install using `wget`:

If not installing using `git`, download and install using `wget`:

```shell
# move to your Home Assistant directory containing the 'config' folder
cd /path/to/home-assistant
# download Addition CA integration archive
wget https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip
# unzip archive
unzip additional_ca.zip
# copy additional_ca integration to Home Assistant custom components
mkdir -p config/custom_components
cp -r additional_ca config/custom_components/
# Installation done, now see Configuration section (README.md)
```

* Download and install manually

  - Click button to download ZIP archive of _Additional CA_ [![Release version](https://img.shields.io/github/v/release/Athozs/hass-additional-ca?color=brightgreen&label=Download&style=for-the-badge)](https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip "Download")
  - Unzip archive
  - Move folder `additional_ca` into `config/custom_components/` directory
  - Installation done, now see Configuration section (README.md)


### 2.2. HAOS - Home Assistant Operating System

To install _Additional CA_ integration without HACS, if you're running Home Assistant from HAOS:

* Go to the [Add-on store](https://my.home-assistant.io/redirect/supervisor_store/)
* Install one of the SSH add-ons (you need to enable "Advanced mode" in your user profile to see them: Click your login name at the bottom left of the screen -> Enable Advanced mode)
* Configure the SSH add-on you chose by following the documentation for it
* Start the SSH add-on
* Connect to the SSH add-on
* Download the latest release of _Additional CA_ from Github (.zip archive):

```shell
wget https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip
```

* Unzip archive:

```shell
unzip additional_ca.zip
```

* Move or copy folder `additional_ca` into `config/custom_components/` directory:

```shell
mkdir -p config/custom_components
cp -r additional_ca config/custom_components/
```


### 2.3. Core

If you're running Home Assistant core (Python package) directly on host, you don't need _Additional CA_ integration. You should update your CA from your host OS.


## 3. CONFIGURATION

For now, _Additional CA_ cannot be configured from UI dashboard. This may be possible in future release.

To configure _Additional CA_ integration, follow these steps:

1. CA files must be in PEM format (often `.crt` or `.pem` extension). Check content with a text editor. Here is an example of a certificate file (the following is a fake):

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
F10YlqcOmeX1uFmKbdi/XorGlkCoMF3TDx8rmp9DBiB
-----END CERTIFICATE-----
```

⚠️ Since Home Assistant core 2024.12.x and newer, Home Assistant includes Python 3.13 and newer which requires to have Certificate Authority with Basic Constraints marked as critical, see an example here: https://github.com/Athozs/hass-additional-ca/issues/13#issuecomment-2645805367 , see why here: https://github.com/home-assistant/core/issues/133506#issuecomment-2573502355

2. Create directory `config/additional_ca` and copy your private CA into it:

```shell
mkdir -p config/additional_ca
cp my_ca.crt config/additional_ca/
```

Optionally, you could group CA into folders.

Directories structure example:

```text
.
├── compose.yml
├── config/
│   ├── additional_ca/
│   │   ├── my_ca.crt
│   │   ├── selfcert.crt
│   │   └── my_folder/
│   │       └── selfcert_2.pem
│   │   └── some_folder/
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

3. Enable _Additional CA_ integration in `configuration.yaml` and set private CA:

_Additional CA_ integration will search into `config/additional_ca/` to find your CA, if your CA has the path `config/additional_ca/my_ca.crt` then your `configuration.yaml` looks like this:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  some_ca: my_ca.crt
# ...
```

Model:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  <string>: <Certificate filename or Certificate relative path as string>
  <string>: <Certificate filename or Certificate relative path as string>
  # ...: ...
```

An other example:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  some_ca: my_ca.crt                               # a cert file
  ca_foo: some_folder/ca2.pem                      # relative path + a cert file
  ca_bar: some_folder/ca3.crt                      # relative path + a cert file
  my_self_signed_cert: selfcert.crt                # a self-signed certificate
  self_signed_crt: my_folder/selfcert_2.pem        # relative path + a self-signed certificate
# ...
```

4. Optionally, if you're running Home Assistant with Docker, set environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`:

Example with Docker Compose:

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

5. Restart Home Assistant.

Some integrations need to be set up all over again to take into account CA trust store (newly including your private CA).

After upgrading Home Assistant to a new version, you need to reboot Home Assistant to load again your certificates.

6. Check the logs, look for pattern `additional_ca` in traces (there is no UI for _Additional CA_).


## 4. UPGRADE

### 4.1. Home Assistant

If you upgrade to a new version of Home Assistant, you need to reboot Home Assistant to load again your certificates with _Additional CA_.


### 4.2. Additional CA

If you upgrade to a new version of _Additional CA_ integration, you need to reboot Home Assistant to load again your certificates.


## 5. HOW DOES _Additional CA_ WORK UNDER THE HOOD ?

### 5.1. Docker

If you're running Home Assistant with Docker:

When enabled, _Additional CA_ integration looks for private Certificates Authorities files (CA) and self-signed certificates in `config/additional_ca` directory.

_Additional CA_ integration loads private CA and self-signed certs only at Home Assistant startup.

_Additional CA_ integration copies private CA and self-signed certs to `/usr/local/share/ca-certificates/` directory inside container and uses `update-ca-certificates` command line to update TLS/SSL trust store.


### 5.2. HAOS - Home Assistant Operating System

HAOS is actually a Linux OS running a `homeassistant` Docker container inside.

If you're running Home Assistant from HAOS or Supervised installation, _Additional CA_ integration works the same way as with Docker, but you can't export environment variable permanently in HAOS, so there is a workaround: _Additional CA_ integration will also add private CA in Certifi CA bundle `/usr/local/lib/python3.xx/site-packages/certifi/cacert.pem` inside `homeassistant` container if not yet present (thanks to @nabbi for the contribution).

Thus, for HAOS, your private CA or self-signed cert will appear in container CA trust store __and__ in Certifi CA bundle (both inside `homeassistant` container).

To show Certifi CA bundle content:

- Turn off Protection mode on SSH add-on in order to enable `docker` CLI (Settings > Add-ons > SSH > turn off Protection mode).
- Connect to HAOS with SSH, then from command line, run:

```shell
# Get certifi bundle path
docker exec homeassistant python -m certifi
# Replace XX with actual Python version
docker exec homeassistant cat "/usr/local/lib/python3.XX/site-packages/certifi/cacert.pem"
```

After upgrading Home Assistant to a new version, you need to reboot Home Assistant to load again your certificates.


## 6. SET `REQUESTS_CA_BUNDLE` ENVIRONMENT VARIABLE

Home Assistant implements a [Python SSL context](https://docs.python.org/3/library/ssl.html#ssl.SSLContext) based on the environment variable `REQUESTS_CA_BUNDLE`.


### 6.1. Docker and Core

If you're running Home Assistant with Docker or Core installation, you may need to set environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` (it won't work permanently on HAOS).

This is optional, it depends on your installed integrations.

Anyway, setting environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` __should not__ break your Home Assistant server.


### 6.2. HAOS - Home Assistant Operating System

 > 📝 __Note__: At time of writing, I could not find on the internet a reliable way to set permanently an environment variable in Home Assistant OS (HAOS). As a workaround, _Additional CA_ integration adds your private CA into Certifi CA bundle if not yet present.


## 7. HOW TO TEST YOUR CA WITH HTTPS

### 7.1. Test with RESTful Command action

After adding your CA, you could create a test action/service to verify **https** connection is working.

- Here is an example of `configuration.yaml` to create an action `RESTful Command: additional_ca_test`:

```yaml
# configuration.yaml

logger:
  default: info

additional_ca:
  my_ca: ca.crt

rest_command:
  additional_ca_test:
    url: "https://your-server.com/"  # <- use your own url here
    method: get
    verify_ssl: true
    timeout: 30

```

- Then run action `RESTful Command: additional_ca_test` from Developer tools panel. Starting from Home Assistant version 2024.2.x, you should see `status: 200` in response to confirm success.
-  If TLS/SSL does not work, you will see error details in Home Assistant logs:

```text
[homeassistant.components.rest_command] Client error. Url: https://your-server.com/. Error: Cannot connect to host your-server.com ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')]
```


### 7.2. Test with `curl`

#### 7.2.1. Docker

To test your CA using `curl`, if you're running Home Assistant with Docker, then from your shell prompt, run:

```shell
docker exec CONTAINER_NAME curl -v -I https://your-server.com
```

You should see an HTTP code 200 to confirm success.


#### 7.2.2. HAOS - Home Assistant Operating System

To test your CA using `curl`, if you're running Home Assistant with HAOS:

- Turn off Protection mode on SSH add-on in order to enable `docker` CLI (Settings > Add-ons > SSH > turn off Protection mode).
- Connect to HAOS with SSH, then from command line, run:

```shell
docker exec homeassistant curl -v -I https://your-server.com
```

You should see an HTTP code 200 to confirm success.


## 8. HOW TO REMOVE A PRIVATE CA ?

To remove your CA: remove or comment CA entry under `additional_ca` domain key in `configuration.yaml`:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  # some_ca: my_ca.crt
# ...
```

Note: `additional_ca` domain key need to be enabled in `configuration.yaml` to remove CA files on next restart of Home Assistant.

Optionally remove your private CA file from `config/additional_ca/` directory.

Then, restart Home Assistant.


## 9. UNINSTALL

To uninstall _Additional CA_ integration, follow these steps:

1. Uninstall it from custom components:

If you installed _Additional CA_ integration from HACS:

* Go to your Home Assistant
* -> HACS
* -> Locate _Additional CA_
* -> Click the three-dots menu in line with _Additional CA_, then click _Remove_

Or if you installed _Additional CA_ integration manually:

```shell
rm -r config/custom_components/additional_ca
```

2. Remove `additional_ca` domain key from `configuration.yaml`:

```yaml
# configuration.yaml
---
default_config:
# additional_ca:
#   some_ca: my_ca.crt
# ...
```

3. Optionally remove `additional_ca` folder containing your private CA:

```shell
rm -r config/additional_ca
```

4. Restart Home Assistant.

If using Docker Compose, recreate container:

```shell
docker compose up -d --force-recreate
```


## 10. TROUBLESHOOTING

Some tips to clean your CA trust store inside Home Assistant in case of failure.


### 10.1. General troubleshooting

* Enable INFO logs level in Home Assistant (see Tips below).
* Check error logs in Home Assistant Settings > System > Logs.
* Some integrations need to be set up all over again to take into account CA trust store (newly including your private CA).


### 10.2. Reset CA trust store of Home Assistant

#### 10.2.1. Docker

To reset CA trust store in Home Assistant with Docker:

- Stop and remove HA container, it will remove all changes made inside container, then start again Home Assistant with Docker.

Otherwise you could do the following:

- Manually remove private CA files from `/usr/local/share/ca-certificates/` directory inside HA container.
- Then update manually CA trust store by running command `update-ca-certificates` inside HA container.


#### 10.2.2. HAOS - Home Assistant Operating System

To reset CA trust store in Home Assistant from HAOS or Supervised installation, you could reset Certifi CA bundle:

- Turn off Protection mode on SSH add-on in order to enable `docker` CLI (Settings > Add-ons > SSH > turn off Protection mode)
- Connect to HAOS with SSH, then from command line, run the following to stop and remove `homeassistant` Docker container inside HAOS and reboot HAOS:

```shell
docker stop homeassistant
docker rm homeassistant
reboot
```

Otherwise you could do the following:

- Download original bundle from https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem
- Replace it at Certifi bundle path
    - To get Certifi bundle path: Connect to HAOS with SSH, then from command line, run `docker exec homeassistant python -m certifi`.


### 10.3. Tips

* To enable INFO logs level, add the following to your `configuration.yaml`:

```yaml
# configuration.yaml
logger:
  default: info
```

* To check your certificate validity, if using x509 certs, run:

```shell
openssl x509 -in config/additional_ca/my_ca.crt -text -noout
```


## 11. KNOWN ISSUES

* In some cases, have to restart twice Home Assistant to take new CA into account, this is due to Home Assistant to create an SSL context before integrations could be loaded.
