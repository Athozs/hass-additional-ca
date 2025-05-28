"""Constants for the Additional CA integration."""

DOMAIN = "additional_ca"

CONFIG_SUBDIR = "additional_ca"

CA_SYSPATH = "/usr/local/share/ca-certificates"

UPDATE_CA_SYSCMD = "update-ca-certificates"

UPDATE_CA_SYSCMD_OPTIONS = "--fresh"

CERTIFI_BACKUP_PATH = "/opt/certifi_original"

NEEDS_RESTART_NOTIF_ID = "hass-additional-ca-needs-restart"
