"""Per-client language: client portal default, visitor switch, and text sent to the client."""

import pytest
from flask_babel import get_locale

from app import db
from app.models import Client


@pytest.fixture(autouse=True)
def disable_audit_logging(monkeypatch):
    monkeypatch.setattr("app.utils.audit.check_audit_table_exists", lambda force_check=False: False)


def _portal_client(test_client, language=None):
    test_client.portal_enabled = True
    test_client.portal_username = "portal-lang"
    test_client.set_portal_password("password123")
    test_client.preferred_language = language
    db.session.commit()
    return test_client.id


def _html_lang(resp):
    return resp.get_data(as_text=True).split('<html lang="', 1)[1].split('"', 1)[0]


@pytest.mark.routes
def test_portal_uses_client_language(app, client, test_client):
    client_id = _portal_client(test_client, "de")
    with client.session_transaction() as sess:
        sess["client_portal_id"] = client_id
    resp = client.get("/client-portal/dashboard")
    assert resp.status_code == 200
    assert _html_lang(resp) == "de"


@pytest.mark.routes
def test_visitor_switch_overrides_client_language_only_in_portal(app, client, test_client):
    client_id = _portal_client(test_client, "de")
    with client.session_transaction() as sess:
        sess["client_portal_id"] = client_id
    resp = client.post(
        "/client-portal/language", data={"language": "fr", "next": "/client-portal/dashboard"}
    )
    assert resp.status_code in (302, 303)
    assert resp.headers["Location"].endswith("/client-portal/dashboard")
    with client.session_transaction() as sess:
        assert sess["portal_language"] == "fr"
        assert "preferred_language" not in sess  # staff UI language untouched
    assert _html_lang(client.get("/client-portal/dashboard")) == "fr"
    assert Client.query.get(client_id).preferred_language == "de"


@pytest.mark.routes
def test_switch_rejects_unknown_language_and_foreign_redirect(app, client, test_client):
    _portal_client(test_client)
    resp = client.post("/client-portal/language", data={"language": "xx", "next": "https://evil.example/"})
    assert resp.status_code in (302, 303)
    assert "evil.example" not in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert "portal_language" not in sess


@pytest.mark.routes
def test_edit_client_saves_language(app, admin_authenticated_client, test_client):
    resp = admin_authenticated_client.post(
        f"/clients/{test_client.id}/edit",
        data={"name": test_client.name, "preferred_language": "de", "prepaid_reset_day": "1"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert Client.query.get(test_client.id).preferred_language == "de"

    admin_authenticated_client.post(
        f"/clients/{test_client.id}/edit",
        data={"name": test_client.name, "preferred_language": "not-a-language", "prepaid_reset_day": "1"},
    )
    assert Client.query.get(test_client.id).preferred_language is None


@pytest.mark.unit
def test_client_locale_forces_language_only_when_set(app, test_client):
    from app.utils.i18n_helpers import client_locale

    with app.test_request_context(headers={"Accept-Language": "fr"}):
        with client_locale(test_client):
            assert str(get_locale()) == "fr"  # no client language: sender's locale stays
        test_client.preferred_language = "de"
        with client_locale(test_client.id):
            assert str(get_locale()) == "de"


@pytest.mark.unit
def test_client_notification_text_is_built_in_client_language(app, test_client, project, monkeypatch):
    from app.services.client_notification_service import ClientNotificationService

    test_client.preferred_language = "de"
    db.session.commit()
    seen = {}

    def fake_create(self, **kwargs):
        seen["locale"] = str(get_locale())

    monkeypatch.setattr(ClientNotificationService, "create_notification", fake_create)
    with app.test_request_context(headers={"Accept-Language": "fr"}):
        ClientNotificationService().notify_project_milestone(project.id, test_client.id, "M1")
    assert seen["locale"] == "de"
