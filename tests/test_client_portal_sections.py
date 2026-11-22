"""The admin's per-client portal customization decides which sections the portal shows."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import ClientPortalCustomization, Invoice, Project, User


@pytest.fixture(autouse=True)
def disable_audit_logging(monkeypatch):
    monkeypatch.setattr("app.utils.audit.check_audit_table_exists", lambda force_check=False: False)


@pytest.fixture
def portal_client(app, client, user, test_client):
    """The test client, logged in to the portal as `user`."""
    User.query.filter_by(id=user.id).update(
        {"client_portal_enabled": True, "client_id": test_client.id}, synchronize_session=False
    )
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
    return client


def _hide(test_client, **shown):
    db.session.add(ClientPortalCustomization(client_id=test_client.id, **shown))
    db.session.commit()


SECTION_URLS = {
    "projects": "/client-portal/projects",
    "invoices": "/client-portal/invoices",
    "time_entries": "/client-portal/time-entries",
    "quotes": "/client-portal/quotes",
}


@pytest.mark.routes
@pytest.mark.parametrize("section", list(SECTION_URLS))
def test_every_section_shown_without_customization(app, portal_client, section):
    assert portal_client.get(SECTION_URLS[section]).status_code == 200
    html = portal_client.get("/client-portal/dashboard").get_data(as_text=True)
    assert f'href="{SECTION_URLS[section]}"' in html


@pytest.mark.routes
@pytest.mark.parametrize("section", list(SECTION_URLS))
def test_hidden_section_is_not_found_and_not_linked(app, portal_client, test_client, section):
    _hide(test_client, **{f"show_{section}": False})

    assert portal_client.get(SECTION_URLS[section]).status_code == 404
    html = portal_client.get("/client-portal/dashboard").get_data(as_text=True)
    assert f'href="{SECTION_URLS[section]}"' not in html
    for other, url in SECTION_URLS.items():
        if other != section:
            assert portal_client.get(url).status_code == 200


@pytest.mark.routes
def test_hidden_invoices_also_block_the_invoice_pages(app, portal_client, user, test_client):
    project = Project(name="Portal Project", client_id=test_client.id)
    db.session.add(project)
    db.session.commit()
    invoice = Invoice(
        invoice_number="INV-SECTIONS",
        project_id=project.id,
        client_name=test_client.name,
        client_id=test_client.id,
        due_date=date.today() + timedelta(days=30),
        created_by=user.id,
        total_amount=Decimal("100.00"),
    )
    db.session.add(invoice)
    db.session.commit()
    page = f"/client-portal/invoices/{invoice.id}"
    assert portal_client.get(page).status_code == 200

    _hide(test_client, show_invoices=False)
    assert portal_client.get(page).status_code == 404
    assert portal_client.get(f"{page}/pdf").status_code == 404


@pytest.mark.routes
def test_hidden_sections_leave_their_dashboard_widgets_out(app, portal_client, test_client):
    _hide(test_client, show_invoices=False, show_projects=False)
    html = portal_client.get("/client-portal/dashboard").get_data(as_text=True)
    assert "Recent invoices" not in html
    assert "Total Invoices" not in html
    assert "Active Projects" not in html
    assert "Total Hours" in html


@pytest.mark.routes
def test_client_edit_page_links_the_portal_customization(app, admin_authenticated_client, test_client):
    html = admin_authenticated_client.get(f"/clients/{test_client.id}/edit").get_data(as_text=True)
    assert f'href="/admin/clients/{test_client.id}/portal-customization"' in html
