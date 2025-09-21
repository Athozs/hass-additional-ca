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

The _Additional CA_ integration for Home Assistant automatically loads a private Certificate Authority or self-signed certificate into Home Assistant to access 3rd-party services with TLS/SSL, even after Home Assistant is upgraded.

## 📘 What does 'private Certificate Authority (CA)' mean here?

* If you manage your own CA, or you trust a specific CA, you will have a `ca.crt` file (or equivalent). This can be called a personal / own / private / custom CA.
* If you generate a self-signed TLS/SSL certificate, you will get a `.crt` file (or equivalent), which is also considered a personal / own / private / custom trusted CA.

📒 This documentation uses 'private CA' or 'self-signed cert' interchangeably for the same purpose.

## 📘 What are the use cases for this integration?

Scenario: You want to import a certificate file into the Home Assistant OS (HAOS) trust store or the Home Assistant Docker container trust store to access a 3rd-party service with TLS/SSL:

* Some of your installed integrations in Home Assistant need to access devices or third-party services with TLS/SSL (HTTPS, etc.), and you have received a `ca.crt` file (or equivalent) from the service provider. ➡ You can load it with the _Additional CA_ integration.
* You have generated a self-signed TLS/SSL certificate for your own service (e.g., a personal HTTPS web server, SMTP, LDAP, etc.) that you want Home Assistant to trust. ➡ You can load it with the _Additional CA_ integration.

![](img/hass-additional-ca.png)


## 📘 Quick Setup (TL;DR)

1. [Install HACS](https://www.hacs.xyz/docs/use/)
2. Install the _Additional CA_ integration via HACS or manually without HACS (full docs below).
3. Copy your private CA to the config folder:

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
  # Optional: force loading additional CAs even if there are already present in system CA
  force_additional_ca: true
# ...
```

4. Restart Home Assistant
5. Done!


___

__Table of contents__

- [Additional CA for Home Assistant](#additional-ca-for-home-assistant)
  - [📘 What does 'private Certificate Authority (CA)' mean here?](#-what-does-private-certificate-authority-ca-mean-here)
  - [📘 What are the use cases for this integration?](#-what-are-the-use-cases-for-this-integration)
  - [📘 Quick Setup (TL;DR)](#-quick-setup-tldr)
  - [1. INSTALL WITH HACS](#1-install-with-hacs)
  - [2. INSTALL WITHOUT HACS](#2-install-without-hacs)
    - [2.1. Docker](#21-docker)
      - [2.1.1. Install using `git`](#211-install-using-git)
      - [2.1.2. Install using `wget`](#212-install-using-wget)
      - [2.1.3 Download and install manually](#213-download-and-install-manually)
    - [2.2. HAOS - Home Assistant Operating System](#22-haos---home-assistant-operating-system)
    - [2.3. Core](#23-core)
  - [3. CONFIGURATION](#3-configuration)
  - [4. UPGRADE](#4-upgrade)
    - [4.1. Home Assistant](#41-home-assistant)
    - [4.2. Additional CA](#42-additional-ca)
  - [5. HOW DOES _Additional CA_ WORK UNDER THE HOOD?](#5-how-does-additional-ca-work-under-the-hood)
    - [5.1. Docker](#51-docker)
    - [5.2. HAOS - Home Assistant Operating System](#52-haos---home-assistant-operating-system)
  - [6. HOW TO TEST YOUR CA WITH HTTPS](#6-how-to-test-your-ca-with-https)
    - [6.1. Test with RESTful Command action](#61-test-with-restful-command-action)
    - [6.2. Test with `curl`](#62-test-with-curl)
      - [6.2.1. Docker](#621-docker)
      - [6.2.2. HAOS - Home Assistant Operating System](#622-haos---home-assistant-operating-system)
  - [7. HOW TO REMOVE A PRIVATE CA?](#7-how-to-remove-a-private-ca)
  - [8. UNINSTALL](#8-uninstall)
  - [9. TROUBLESHOOTING](#9-troubleshooting)
    - [9.1. General troubleshooting](#91-general-troubleshooting)
    - [9.2. Reset CA trust store of Home Assistant](#92-reset-ca-trust-store-of-home-assistant)
      - [9.2.1. Docker](#921-docker)
      - [9.2.2. HAOS - Home Assistant Operating System](#922-haos---home-assistant-operating-system)
    - [9.3. Tips](#93-tips)
  - [10. KNOWN ISSUES](#10-known-issues)


## 1. INSTALL WITH HACS

To install the _Additional CA_ integration with HACS:

* [Install HACS](https://hacs.xyz/docs/use/) if not already done.
* Then, go to your Home Assistant instance,
    * -> HACS
    * -> Search for "Additional CA"
    * -> Click the three-dots menu for _Additional CA_, then click _Download_

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

#### 2.1.1. Install using `git`

Download and install using `git`:

```shell
# move to your Home Assistant directory containing the 'config' folder
cd /path/to/home-assistant
# git clone Addition CA integration
git clone https://github.com/Athozs/hass-additional-ca.git
# copy additional_ca integration to Home Assistant custom components
mkdir -p config/custom_components
cp -r hass-additional-ca/custom_components/additional_ca config/custom_components/
# Installation is done, now see section [Configuration](#3-configuration) in this README.md
```

#### 2.1.2. Install using `wget`

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
# Installation is done, now see section [Configuration](#3-configuration) in this README.md
```

#### 2.1.3 Download and install manually

- Click the button to download the ZIP archive of _Additional CA_ [![Release version](https://img.shields.io/github/v/release/Athozs/hass-additional-ca?color=brightgreen&label=Download&style=for-the-badge)](https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip "Download")
- Unzip the archive.
- Move the `additional_ca` folder into the `config/custom_components/` directory.
- Installation is done. Now, see the section [Configuration](#3-configuration) in this README.md.


### 2.2. HAOS - Home Assistant Operating System

To install the _Additional CA_ integration without HACS if you're running Home Assistant from HAOS:

* Go to the [Add-on store](https://my.home-assistant.io/redirect/supervisor_store/)
* Install one of the SSH add-ons (you need to enable "Advanced mode" in your user profile to see them: Click your login name at the bottom left of the screen -\> Enable Advanced mode)
* Configure your chosen SSH add-on by following its documentation.
* Start the SSH add-on
* Connect to the SSH add-on
* Download the latest release of _Additional CA_ from GitHub (the .zip archive):

```shell
wget https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip
```

* Unzip the archive:

```shell
unzip additional_ca.zip
```

* Move or copy the `additional_ca` folder into the `config/custom_components/` directory:

```shell
mkdir -p config/custom_components
cp -r additional_ca config/custom_components/
```


### 2.3. Core

If you're running Home Assistant Core (as a Python package) directly on the host, you don't need the _Additional CA_ integration. You should update the CAs from your host OS.


## 3. CONFIGURATION

For now, _Additional CA_ cannot be configured from the UI dashboard. This may be possible in a future release.

To configure the _Additional CA_ integration, follow these steps:

1. CA files must be in PEM format (often with a `.crt` or `.pem` extension). You can check the content with a text editor. Here is an example of a certificate file (the following is a fake):

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

⚠️ Since Home Assistant Core 2024.12.x and newer, Home Assistant includes Python 3.13 and newer, which requires the Certificate Authority to have Basic Constraints marked as critical, see an example here: [Athozs/hass-additional-ca/issues/13#issuecomment-2645805367](https://github.com/Athozs/hass-additional-ca/issues/13#issuecomment-2645805367), see why here: [home-assistant/core/issues/133506#issuecomment-2573502355](https://github.com/home-assistant/core/issues/133506#issuecomment-2573502355).

2. Create the directory `config/additional_ca` and copy your private CA into it:

```shell
mkdir -p config/additional_ca
cp my_ca.crt config/additional_ca/
```

Optionally, you can group CAs into subfolders.

Directory structure example:

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

3. Enable the _Additional CA_ integration in `configuration.yaml` and set the private CA:

The _Additional CA_ integration will search in `config/additional_ca/` to find your CA. If your CA has the path `config/additional_ca/my_ca.crt`, then your `configuration.yaml` should look like this:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  some_ca: my_ca.crt
# ...
```

You can also force the integration to load additional CAs, even if there are already present in system CA, by setting the `force_additional_ca` option to `true`. Valid true values for `force_additional_ca` are: `True`, `true`, `1`, `yes`, `on`.

Example:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  some_ca: my_ca.crt
  force_additional_ca: true
# ...
```

Model:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  <string>: <Certificate filename or Certificate relative path as string>
  force_additional_ca: true  # Optional, boolean
  # ...: ...
```

Another example:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  force_additional_ca: true                        # Optional, boolean
  some_ca: my_ca.crt                               # a cert file
  ca_foo: some_folder/ca2.pem                      # relative path + a cert file
  ca_bar: some_folder/ca3.crt                      # relative path + a cert file
  my_self_signed_cert: selfcert.crt                # a self-signed certificate
  self_signed_crt: my_folder/selfcert_2.pem        # relative path + a self-signed certificate
# ...
```

4. Restart Home Assistant.

> [!IMPORTANT]
> Some integrations need to be set up again to use the updated CA trust store (which now includes your private CA).
>
> After upgrading Home Assistant to a new version, you need to restart Home Assistant to load your certificates again.

5. Check the logs. Look for the pattern `additional_ca` in the traces (there is no UI for _Additional CA_).


## 4. UPGRADE

### 4.1. Home Assistant

If you upgrade to a new version of Home Assistant, you need to restart Home Assistant to load your certificates again with _Additional CA_.


### 4.2. Additional CA

If you upgrade to a new version of the _Additional CA_ integration, you need to restart Home Assistant to load your certificates again.


## 5. HOW DOES _Additional CA_ WORK UNDER THE HOOD?

### 5.1. Docker

If you're running Home Assistant with Docker:

When enabled, the _Additional CA_ integration looks for private Certificate Authority (CA) files and self-signed certificates in the `config/additional_ca/` directory.

The _Additional CA_ integration loads private CAs and self-signed certs only at Home Assistant startup.

The _Additional CA_ integration copies the private CAs and self-signed certs to the `/usr/local/share/ca-certificates/` directory inside the container and runs the `update-ca-certificates` command to update the TLS/SSL trust store at `/etc/ssl/certs/ca-certificates.crt`.

> [!NOTE]
> In earlier versions of _Additional CA_ (0.4.x and below), you needed to set the `REQUESTS_CA_BUNDLE` environment variable for certificate verification. This is no longer required. The integration now uses the `certifi-linux` Python package, which automatically points Certifi to the system CA bundle at `/etc/ssl/certs/ca-certificates.crt`.


### 5.2. HAOS - Home Assistant Operating System

HAOS is actually a Linux-based OS that runs a `homeassistant` Docker container inside.

If you're running Home Assistant from a HAOS or Supervised installation, the _Additional CA_ integration works the same way as with Docker.

To show the system CA content:

- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS with SSH, then from the command line, run:

```shell
docker exec homeassistant cat "/etc/ssl/certs/ca-certificates.crt"
```


## 6. HOW TO TEST YOUR CA WITH HTTPS

### 6.1. Test with RESTful Command action

After adding your CA, you can create a test action/service to verify that the __https__ connection is working.

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

- Then, run the action `RESTful Command: additional_ca_test` from the Developer Tools panel. You should see `status: 200` in the response to confirm success.
- If TLS/SSL does not work, you will see error details in the Home Assistant logs:

```text
[homeassistant.components.rest_command] Client error. Url: https://your-server.com/.
Error: Cannot connect to host your-server.com ssl:True
[SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate (_ssl.c:1006)')]
```


### 6.2. Test with `curl`

#### 6.2.1. Docker

To test your CA using `curl`, if you're running Home Assistant with Docker, then from your shell prompt, run:

```shell
docker exec CONTAINER_NAME curl -v -I https://your-server.com
```

You should see an HTTP code 200 to confirm success.

#### 6.2.2. HAOS - Home Assistant Operating System

To test your CA using `curl`, if you're running Home Assistant with HAOS:

- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS via SSH, then from the command line, run:

```shell
docker exec homeassistant curl -v -I https://your-server.com
```

You should see an HTTP code 200 to confirm success.


## 7. HOW TO REMOVE A PRIVATE CA?

To remove your CA: remove or comment out the CA entry under the `additional_ca` domain key in `configuration.yaml`:

```yaml
# configuration.yaml
---
default_config:
additional_ca:
  # some_ca: my_ca.crt
# ...
```

Note: The `additional_ca` domain key needs to be present (even if empty) in `configuration.yaml` for the integration to remove the CA files on the next Home Assistant restart.

Optionally, remove your private CA file from the `config/additional_ca/` directory.

Then, reset system CA of Home Assistant, see section [Reset CA trust store of Home Assistant](#92-reset-ca-trust-store-of-home-assistant) in this README.md.


## 8. UNINSTALL

To uninstall the _Additional CA_ integration, follow these steps:

1. Uninstall it from `custom_components`:

If you installed the _Additional CA_ integration via HACS:

* Go to your Home Assistant
* -> HACS
* -> Locate _Additional CA_
* -> Click the three-dots menu for _Additional CA_, then click _Remove_

Or, if you installed the _Additional CA_ integration manually:

```shell
rm -r config/custom_components/additional_ca
```

2. Remove the `additional_ca` domain key from `configuration.yaml`:

```yaml
# configuration.yaml
---
default_config:
# additional_ca:
#   some_ca: my_ca.crt
# ...
```

3. Optionally, remove the `additional_ca` folder containing your private CAs:

```shell
rm -r config/additional_ca
```

4. Restart Home Assistant.

If you are using Docker Compose, recreate the container:

```shell
docker compose up -d --force-recreate
```


## 9. TROUBLESHOOTING

Some tips for cleaning your CA trust store inside Home Assistant in case of failure.


### 9.1. General troubleshooting

* Enable the INFO log level in Home Assistant (see Tips below).
* Check the error logs in Home Assistant at Settings \> System \> Logs.
* Some integrations need to be set up again to use the updated CA trust store (which now includes your private CA).


### 9.2. Reset CA trust store of Home Assistant

#### 9.2.1. Docker

To reset the CA trust store in Home Assistant with Docker:

- Stop and remove the HA container. This will remove all changes made inside the container. Then, start Home Assistant with Docker again.

Alternatively, you can do the following:

- Manually remove the private CA files from the `/usr/local/share/ca-certificates/` directory inside the HA container.
- Then, manually update the CA trust store by running the command `update-ca-certificates` inside the HA container.

#### 9.2.2. HAOS - Home Assistant Operating System

To reset the CA trust store in Home Assistant from a HAOS or Supervised installation:

- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS via SSH, then from the command line, run the following to stop and remove the `homeassistant` Docker container inside HAOS and reboot HAOS:

```shell
docker stop homeassistant
docker rm homeassistant
reboot
```


### 9.3. Tips

* To enable the INFO log level, add the following to your `configuration.yaml`:

```yaml
# configuration.yaml
logger:
  default: info
```

* To check your certificate's validity, if using x509 certs, run:

```shell
openssl x509 -in config/additional_ca/my_ca.crt -text -noout
```


## 10. KNOWN ISSUES

* In some cases, you may have to restart Home Assistant twice for the new CA to be taken into account. This is due to Home Assistant creating an SSL context before integrations can be loaded.
