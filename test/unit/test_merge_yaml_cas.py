"""Tests for merge_yaml_cas."""

from custom_components.additional_ca.utils import merge_yaml_cas


def _ca(file, enabled=True, source="ui"):
    return {"file": file, "enabled": enabled, "source": source}


def test_yaml_cas_are_added_enabled():
    assert merge_yaml_cas({}, {"a": "a.crt"}) == {"a": _ca("a.crt", source="yaml")}


def test_yaml_cas_keep_enabled_state_and_follow_yaml():
    existing = {"a": _ca("old.crt", enabled=False, source="yaml")}
    assert merge_yaml_cas(existing, {"a": "new.crt"}) == {"a": _ca("new.crt", False, "yaml")}


def test_removed_yaml_cas_are_dropped():
    existing = {"a": _ca("a.crt", source="yaml")}
    assert merge_yaml_cas(existing, {}) == {}


def test_ui_cas_are_preserved():
    existing = {"u": _ca("ui/u.crt", enabled=False)}
    assert merge_yaml_cas(existing, {"a": "a.crt"}) == {
        "u": _ca("ui/u.crt", False),
        "a": _ca("a.crt", source="yaml"),
    }


def test_deprecated_force_option_is_ignored():
    assert merge_yaml_cas({}, {"force_additional_ca": "True"}) == {}
