"""Constants for the Additional CA integration."""

DOMAIN = "additional_ca"

CONFIG_SUBDIR = "additional_ca"

# Subfolder of CONFIG_SUBDIR where certificates uploaded from the UI are stored
UI_CA_SUBDIR = "ui"

UI_CA_EXTENSION = ".crt"

CA_SYSPATH = "/usr/local/share/ca-certificates"

UPDATE_CA_SYSCMD = "update-ca-certificates"

UPDATE_CA_SYSCMD_OPTIONS = "--fresh"

# Deprecated option 'force_additional_ca' (boolean), to be removed from code in future
FORCE_ADDITIONAL_CA = "force_additional_ca"

NEEDS_RESTART_ISSUE_ID = "hass-additional-ca-needs-restart"

# Config entry options: {CONF_CAS: {ca_name: {CONF_FILE, CONF_ENABLED, CONF_SOURCE}}}
CONF_CAS = "cas"
CONF_FILE = "file"
CONF_ENABLED = "enabled"
CONF_SOURCE = "source"
CONF_CERTIFICATE = "certificate"
CONF_DELETE = "delete"

SOURCE_YAML = "yaml"
SOURCE_UI = "ui"

# hass.data key holding the content of the 'additional_ca' key from configuration.yaml
DATA_YAML_CONFIG = f"{DOMAIN}_yaml_config"
