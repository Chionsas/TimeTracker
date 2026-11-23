"""ENABLED_LANGUAGES narrows the languages every picker offers."""

import importlib.util
import os
import re

import pytest

CONFIG_PY = os.path.join(os.path.dirname(__file__), "..", "app", "config.py")


def _languages_with(monkeypatch, value):
    """Config.LANGUAGES as app/config.py builds it with ENABLED_LANGUAGES set to `value`.

    Loaded afresh, as app/config/__init__.py loads it, since the class reads the
    environment when it is defined.
    """
    if value is None:
        monkeypatch.delenv("ENABLED_LANGUAGES", raising=False)
    else:
        monkeypatch.setenv("ENABLED_LANGUAGES", value)
    spec = importlib.util.spec_from_file_location("config_under_test", CONFIG_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Config.LANGUAGES


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected",
    [
        ("en,lt", ["en", "lt"]),
        (" lt , en ", ["en", "lt"]),
        ("lt,xx", ["lt"]),
    ],
)
def test_enabled_languages_narrow_the_list(monkeypatch, value, expected):
    assert list(_languages_with(monkeypatch, value)) == expected


@pytest.mark.unit
@pytest.mark.parametrize("value", [None, "", "xx,yy"])
def test_without_valid_codes_every_language_stays(monkeypatch, value):
    languages = _languages_with(monkeypatch, value)
    assert {"en", "de", "lt", "fr"} <= set(languages)


@pytest.mark.routes
def test_portal_switcher_offers_only_enabled_languages(app, client, monkeypatch):
    monkeypatch.setattr("app.utils.audit.check_audit_table_exists", lambda force_check=False: False)
    app.config["LANGUAGES"] = {"en": "English", "lt": "Lietuvių"}
    html = client.get("/client-portal/login").get_data(as_text=True)
    switcher = html[html.index('name="language"') :]
    switcher = switcher[: switcher.index("</select>")]
    assert re.findall(r'<option value="([a-z]+)"', switcher) == ["en", "lt"]
