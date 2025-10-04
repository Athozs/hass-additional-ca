"""Constants for the Additional CA integration."""

DOMAIN = "additional_ca"

CONFIG_SUBDIR = "additional_ca"

CA_SYSPATH = "/usr/local/share/ca-certificates"

UPDATE_CA_SYSCMD = "update-ca-certificates"

UPDATE_CA_SYSCMD_OPTIONS = "--fresh"

# Deprecated option 'force_additional_ca' (boolean), to be removed from code in future
FORCE_ADDITIONAL_CA = "force_additional_ca"

NEEDS_RESTART_NOTIF_ID = "hass-additional-ca-needs-restart"
