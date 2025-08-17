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

The *Additional CA* integration for Home Assistant automatically loads a private Certificate Authority or self-signed certificate into Home Assistant to access 3rd-party services with TLS/SSL, even after Home Assistant is upgraded.

## 📘 What is a private Certificate Authority (CA)?

* If you manage your own CA, or you trust a specific CA, you will have a `ca.crt` file (or equivalent). This can be called a personal / own / private / custom CA.
* If you generate a self-signed TLS/SSL certificate, you will get a `.crt` file (or equivalent), which is also considered a personal / own / private / custom trusted CA.

📒 This documentation uses 'private CA' or 'self-signed cert' interchangeably for the same purpose.

## 📘 What are the use cases for this integration?

Scenario: You want to import a certificate file into the Home Assistant OS (HAOS) trust store or the Home Assistant Docker container trust store to access a 3rd-party service with TLS/SSL:

* Some of your installed integrations in Home Assistant need to access devices or third-party services with TLS/SSL (HTTPS, etc.), and you have received a `ca.crt` file (or equivalent) from the service provider. ➡ You can load it with the *Additional CA* integration.
* You have generated a self-signed TLS/SSL certificate for your own service (e.g., a personal HTTPS web server, SMTP, LDAP, etc.) that you want Home Assistant to trust. ➡ You can load it with the *Additional CA* integration.

![](img/hass-additional-ca.png)

## 📘 Quick Setup (TL;DR)

1. [Install HACS](https://www.hacs.xyz/docs/use/)
2. Install the *Additional CA* integration via HACS or manually without HACS (full docs below).
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
   # ...
   ```
4. Export an environment variable if running Home Assistant with Docker (not needed for Home Assistant OS (HAOS) installations):
   ```yaml
   # compose.yml
   version: '3'
   services:
     homeassistant:
       # ...
       environment:
         - REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
   ```
5. Restart Home Assistant.
6. Done!

-----

# Table of contents

- [Additional CA for Home Assistant](#additional-ca-for-home-assistant)
  - [📘 What is a private Certificate Authority (CA)?](#-what-is-a-private-certificate-authority-ca)
  - [📘 What are the use cases for this integration?](#-what-are-the-use-cases-for-this-integration)
  - [📘 Quick Setup (TL;DR)](#-quick-setup-tldr)
  - [1. INSTALL WITH HACS](#1-install-with-hacs)
  - [2. INSTALL WITHOUT HACS](#2-install-without-hacs)
    - [2.1. Docker](#21-docker)
      - [2.1.1. Install using `git`](#211-install-using-git)
      - [2.1.2. Install using `wget`](#212-install-using-wget)
      - [2.1.3. Download & install manually](#213-download-and-install-manually)
    - [2.2. HAOS - Home Assistant Operating System](#22-haos---home-assistant-operating-system)
    - [2.3. Core](#23-core)
  - [3. CONFIGURATION](#3-configuration)
  - [4. UPGRADE](#4-upgrade)
    - [4.1. Home Assistant](#41-home-assistant)
    - [4.2. Additional CA](#42-additional-ca)
  - [5. HOW DOES Additional CA WORK UNDER THE HOOD?](#5-how-does-additional-ca-work-under-the-hood)
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
  - [8. HOW TO REMOVE A PRIVATE CA?](#8-how-to-remove-a-private-ca)
  - [9. UNINSTALL](#9-uninstall)
  - [10. TROUBLESHOOTING](#10-troubleshooting)
    - [10.1. General troubleshooting](#101-general-troubleshooting)
    - [10.2. Reset CA trust store of Home Assistant](#102-reset-ca-trust-store-of-home-assistant)
      - [10.2.1. Docker](#1021-docker)
      - [10.2.2. HAOS - Home Assistant Operating System](#1022-haos---home-assistant-operating-system)
    - [10.3. Tips](#103-tips)
  - [11. KNOWN ISSUES](#11-known-issues)

# 1. INSTALL WITH HACS

To install the *Additional CA* integration with HACS:

* [Install HACS](https://hacs.xyz/docs/use/) if not already done.
* Then, in your Home Assistant instance:
  * &rarr; HACS
  * &rarr; Search for "Additional CA"
  * &rarr; Click the three-dots menu for *Additional CA* and then click *Download*.
 
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

# 2. INSTALL WITHOUT HACS

## 2.1. Docker

To install the *Additional CA* integration without HACS, if you're running Home Assistant with Docker, you can use `git` or `wget`.

### 2.1.1. Install using `git`

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

### 2.1.2. Install using `wget`

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

### 2.1.3 Download and install manually

      - Click the button to download the ZIP archive of *Additional CA* [](https://github.com/Athozs/hass-additional-ca/releases/latest/download/additional_ca.zip "Download")
      - Unzip the archive.
      - Move the `additional_ca` folder into the `config/custom_components/` directory.
      - Installation is done. Now, see the Configuration section (README.md).

## 2.2. HAOS - Home Assistant Operating System

To install the *Additional CA* integration without HACS if you're running Home Assistant from HAOS:

* Go to the [Add-on store](https://my.home-assistant.io/redirect/supervisor_store/).
* Install one of the SSH add-ons (you need to enable "Advanced mode" in your user profile to see them: Click your login name at the bottom left of the screen -\> Enable Advanced mode).
* Configure your chosen SSH add-on by following its documentation.
* Start the SSH add-on.
* Connect to the SSH add-on.
* Download the latest release of *Additional CA* from GitHub (the .zip archive):
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

## 2.3. Core

If you're running Home Assistant Core (as a Python package) directly on the host, you don't need the *Additional CA* integration. You should update the CAs from your host OS.

# 3. CONFIGURATION

For now, *Additional CA* cannot be configured from the UI dashboard. This may be possible in a future release.

To configure the *Additional CA* integration, follow these steps:

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
   ⚠️ Since Home Assistant Core 2024.12.x and newer, Home Assistant includes Python 3.13 and newer, which requires the Certificate Authority to have Basic Constraints marked as critical, see an example [here](https://github.com/Athozs/hass-additional-ca/issues/13#issuecomment-2645805367), see why [here](https://github.com/home-assistant/core/issues/133506#issuecomment-2573502355).
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
3. Enable the *Additional CA* integration in `configuration.yaml` and set the private CA:
   The *Additional CA* integration will search in `config/additional_ca/` to find your CA. If your CA has the path `config/additional_ca/my_ca.crt`, then your `configuration.yaml` should look like this:
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
   Another example:
   ```yaml
   # configuration.yaml
   ---
   default_config:
   additional_ca:
     some_ca: my_ca.crt                      # a cert file
     ca_foo: some_folder/ca2.pem             # relative path + a cert file
     ca_bar: some_folder/ca3.crt             # relative path + a cert file
     my_self_signed_cert: selfcert.crt       # a self-signed certificate
     self_signed_crt: my_folder/selfcert_2.pem     # relative path + a self-signed certificate
   # ...
   ```
4. Optionally, if you're running Home Assistant with Docker, set the environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`:
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
> [!IMPORTANT]
> Some integrations need to be set up again to use the updated CA trust store (which now includes your private CA).
> 
> After upgrading Home Assistant to a new version, you need to restart Home Assistant to load your certificates again.

6. Check the logs. Look for the pattern `additional_ca` in the traces (there is no UI for *Additional CA*).

# 4. UPGRADE

## 4.1. Home Assistant

If you upgrade to a new version of Home Assistant, you need to restart Home Assistant to load your certificates again with *Additional CA*.

## 4.2. Additional CA

If you upgrade to a new version of the *Additional CA* integration, you need to restart Home Assistant to load your certificates again.

# 5. HOW DOES *Additional CA* WORK UNDER THE HOOD?

## 5.1. Docker

If you're running Home Assistant with Docker:

* When enabled, the *Additional CA* integration looks for private Certificate Authority (CA) files and self-signed certificates in the `config/additional_ca` directory.
* The *Additional CA* integration loads private CAs and self-signed certs only at Home Assistant startup.
* The *Additional CA* integration copies the private CAs and self-signed certs to the `/usr/local/share/ca-certificates/` directory inside the container and runs the `update-ca-certificates` command to update the TLS/SSL trust store.

## 5.2. HAOS - Home Assistant Operating System

HAOS is a Linux-based OS that runs a `homeassistant` Docker container.

If you're running Home Assistant from a HAOS or Supervised installation, the *Additional CA* integration works the same way as with Docker. However, you can't permanently export an environment variable in HAOS, so there is a workaround: The *Additional CA* integration will also add the private CA to the Certifi CA bundle at `/usr/local/lib/python3.xx/site-packages/certifi/cacert.pem` inside the `homeassistant` container if it is not already present (thanks to @nabbi for the contribution).

Thus, for HAOS, your private CA or self-signed cert will appear in the container's CA trust store **and** in the Certifi CA bundle (both are inside the `homeassistant` container).

To show the Certifi CA bundle content:
- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS with SSH, then from the command line, run:
  ```shell
  # Get Certifi bundle path
  docker exec homeassistant python -m certifi
  # Replace XX with the actual Python version
  docker exec homeassistant cat "/usr/local/lib/python3.XX/site-packages/certifi/cacert.pem"
  ```
After upgrading Home Assistant to a new version, you need to restart Home Assistant to load your certificates again.

# 6. SET `REQUESTS_CA_BUNDLE` ENVIRONMENT VARIABLE

Home Assistant implements a [Python SSL context](https://docs.python.org/3/library/ssl.html#ssl.SSLContext) based on the environment variable `REQUESTS_CA_BUNDLE`.

## 6.1. Docker and Core

If you're running Home Assistant with a Docker or Core installation, you may need to set the environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` (this will not work permanently on HAOS).

This is optional; it depends on your installed integrations.

Anyway, setting the environment variable `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` **should not** break your Home Assistant server.

## 6.2. HAOS - Home Assistant Operating System

> [!NOTE]
> At the time of writing, there is no reliable way to permanently set an environment variable in Home Assistant OS (HAOS). As a workaround, the *Additional CA* integration adds your private CA to the Certifi CA bundle if it is not already present.

# 7. HOW TO TEST YOUR CA WITH HTTPS

## 7.1. Test with RESTful Command action

After adding your CA, you can create a test action/service to verify that the **https** connection is working.

- Here is an example `configuration.yaml` to create an action `RESTful Command: additional_ca_test`:
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
- Then, run the action `RESTful Command: additional_ca_test` from the Developer Tools panel. Starting from Home Assistant version 2024.2.x, you should see `status: 200` in the response to confirm success.
- If TLS/SSL does not work, you will see error details in the Home Assistant logs:
  ```text
  [homeassistant.components.rest_command] Client error. Url: https://your-server.com/. Error: Cannot connect to host your-server.com ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')]
  ```

## 7.2. Test with `curl`

### 7.2.1. Docker

To test your CA using `curl`, if you're running Home Assistant with Docker, then from your shell prompt, run:

```shell
docker exec CONTAINER_NAME curl -v -I https://your-server.com
```

You should see an HTTP code 200 to confirm success.

### 7.2.2. HAOS - Home Assistant Operating System

To test your CA using `curl`, if you're running Home Assistant with HAOS:
- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS via SSH, then from the command line, run:
  ```shell
  docker exec homeassistant curl -v -I https://your-server.com
  ```
You should see an HTTP code 200 to confirm success.

# 8. HOW TO REMOVE A PRIVATE CA?

1. To remove your CA, remove or comment out the CA entry under the `additional_ca` domain key in `configuration.yaml`:
   ```yaml
   # configuration.yaml
   ---
   default_config:
   additional_ca:
     # some_ca: my_ca.crt
   # ...
   ```
   Note: The `additional_ca` domain key needs to be present (even if empty) in `configuration.yaml` for the integration to remove the CA files on the next Home Assistant restart.
2. Optionally, remove your private CA file from the `config/additional_ca/` directory.
3. Then, restart Home Assistant.

# 9. UNINSTALL

To uninstall the *Additional CA* integration, follow these steps:

1. Uninstall it from `custom_components`:
   - If you installed the *Additional CA* integration via HACS:
     * Go to your Home Assistant.
     * &rarr; HACS
     * &rarr; Find *Additional CA*.
     * &rarr; Click the three-dots menu for *Additional CA* and then click *Remove*.
   - Or, if you installed the *Additional CA* integration manually:
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

# 10. TROUBLESHOOTING

Some tips for cleaning your CA trust store inside Home Assistant in case of failure.

## 10.1. General troubleshooting

* Enable the INFO log level in Home Assistant (see Tips below).
* Check the error logs in Home Assistant at Settings \> System \> Logs.
* Some integrations need to be set up again to use the updated CA trust store (which now includes your private CA).

## 10.2. Reset CA trust store of Home Assistant

### 10.2.1. Docker

To reset the CA trust store in Home Assistant with Docker:

- Stop and remove the HA container. This will remove all changes made inside the container. Then, start Home Assistant with Docker again.

Alternatively, you can do the following:

- Manually remove the private CA files from the `/usr/local/share/ca-certificates/` directory inside the HA container.
- Then, manually update the CA trust store by running the command `update-ca-certificates` inside the HA container.

### 10.2.2. HAOS - Home Assistant Operating System

To reset the CA trust store in Home Assistant from a HAOS or Supervised installation, you can reset the Certifi CA bundle:

- Turn off Protection mode in the SSH add-on to enable the `docker` CLI (Settings \> Add-ons \> SSH \> turn off Protection mode).
- Connect to HAOS via SSH, then from the command line, run the following to stop and remove the `homeassistant` Docker container inside HAOS and reboot HAOS:
  ```shell
  docker stop homeassistant
  docker rm homeassistant
  reboot
  ```

Alternatively, you can do the following:

- Download the original bundle from [https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem](https://raw.githubusercontent.com/certifi/python-certifi/master/certifi/cacert.pem)
- Replace the file at the Certifi bundle path.
- To get the Certifi bundle path, connect to HAOS via SSH, then from the command line, run `docker exec homeassistant python -m certifi`.

## 10.3. Tips

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

# 11. KNOWN ISSUES

* In some cases, you may have to restart Home Assistant twice for the new CA to be taken into account. This is due to Home Assistant creating an SSL context before integrations can be loaded.
