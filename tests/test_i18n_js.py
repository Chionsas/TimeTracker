"""
gettext for JavaScript: the /i18n/<locale>.js catalog (app/routes/i18n.py) and
the browser runtime (app/static/i18n.js).
"""

import importlib.util
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
from flask import render_template_string

from app import create_app

pytestmark = [pytest.mark.unit]

PO = textwrap.dedent(
    """\
    msgid ""
    msgstr ""
    "Content-Type: text/plain; charset=utf-8\\n"
    "Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2);\\n"

    #: app/static/idle.js:12
    msgid "Timer stopped"
    msgstr "Laikmatis sustabdytas"

    #: app/templates/base.html:5
    #: app/static/js/command-palette.js:40
    msgid "Start Timer"
    msgstr "Paleisti laikmatį"

    #: app/templates/base.html:7
    msgid "Template only"
    msgstr "Tik šablone"

    #: app/static/idle.js:30
    #, fuzzy
    msgid "Fuzzy"
    msgstr "Neaiškus"

    #: app/static/idle.js:31
    msgid "Untranslated"
    msgstr ""

    #: app/static/idle.js:40
    msgid "Line separator"
    msgstr "a b"

    #: app/static/activity-feed.js:9
    msgid "%(num)s day"
    msgid_plural "%(num)s days"
    msgstr[0] "%(num)s diena"
    msgstr[1] "%(num)s dienos"
    msgstr[2] "%(num)s dienų"
    """
)


@pytest.fixture
def app(app_config, tmp_path):
    po_dir = tmp_path / "translations" / "eo" / "LC_MESSAGES"
    po_dir.mkdir(parents=True)
    (po_dir / "messages.po").write_text(PO, encoding="utf-8")
    config = dict(app_config)
    config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'test.sqlite'}"
    config["BABEL_TRANSLATION_DIRECTORIES"] = str(tmp_path / "translations")
    app = create_app(config)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class TestCatalogRoute:
    def test_ships_only_javascript_strings(self, client):
        res = client.get("/i18n/eo.js")
        assert res.status_code == 200
        assert res.mimetype == "application/javascript"
        body = res.get_data(as_text=True)
        assert body.startswith("window.i18n = {")
        assert '"Timer stopped": "Laikmatis sustabdytas"' in body
        # Located in a template and a JS file: needed by both.
        assert '"Start Timer": "Paleisti laikmatį"' in body
        assert "Template only" not in body
        assert "Fuzzy" not in body
        assert "Untranslated" not in body
        # U+2028 ends a string literal in older JavaScript engines.
        assert '"Line separator": "a\\u2028b"' in body

    def test_plural_forms(self, client):
        body = client.get("/i18n/eo.js").get_data(as_text=True)
        assert '"%(num)s day": ["%(num)s diena", "%(num)s dienos", "%(num)s dienų"]' in body
        assert "plural: function (n) { return Number((n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)); }" in body

    def test_locale_without_catalog_is_empty(self, client):
        body = client.get("/i18n/en.js").get_data(as_text=True)
        assert "catalog: {}" in body
        assert "return Number((n != 1));" in body

    def test_rejects_malformed_locale(self, client):
        assert client.get("/i18n/..%2Fetc.js").status_code == 404
        assert client.get("/i18n/x.js").status_code == 404

    def test_caching(self, client):
        res = client.get("/i18n/eo.js")
        etag = res.headers["ETag"]
        assert res.headers["Cache-Control"] == "no-cache"
        assert client.get("/i18n/eo.js", headers={"If-None-Match": etag}).status_code == 304
        hashed = client.get(f"/i18n/eo.js?v={etag}")
        assert hashed.headers["Cache-Control"] == "public, max-age=31536000, immutable"

    def test_template_global_points_at_current_locale(self, app):
        with app.test_request_context(headers={"Accept-Language": "eo"}):
            app.config["LANGUAGES"] = {**app.config["LANGUAGES"], "eo": "Test"}
            url = render_template_string("{{ i18n_catalog_url() }}")
        assert url.startswith("/i18n/eo.js?v=")
        assert url.split("v=")[1] == app.test_client().get("/i18n/eo.js").headers["ETag"]


RUNTIME_CHECK = textwrap.dedent(
    """\
    const assert = require('assert');
    const vm = require('vm');
    const fs = require('fs');
    const window = {};
    vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), { window });
    const { gettext, ngettext } = window;

    // No catalog loaded: English, placeholders filled.
    assert.strictEqual(gettext('Timer stopped'), 'Timer stopped');
    assert.strictEqual(gettext('%(count)s left, 100%%', { count: 3 }), '3 left, 100%');
    assert.strictEqual(gettext('%(missing)s stays'), '%(missing)s stays');
    assert.strictEqual(ngettext('%(num)s day', '%(num)s days', 1), '1 day');
    assert.strictEqual(ngettext('%(num)s day', '%(num)s days', 2), '2 days');

    window.i18n = {
      locale: 'xx',
      plural: function (n) { return Number((n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)); },
      catalog: {
        'Timer stopped': 'Laikmatis sustabdytas',
        'Empty': '',
        '%(num)s day': ['%(num)s diena', '%(num)s dienos', '%(num)s dienų'],
        '%(name)s said': '%(name)s sakė',
      },
    };
    assert.strictEqual(gettext('Timer stopped'), 'Laikmatis sustabdytas');
    assert.strictEqual(gettext('Empty'), 'Empty');
    assert.strictEqual(gettext('%(name)s said', { name: 'Ona' }), 'Ona sakė');
    assert.strictEqual(ngettext('%(num)s day', '%(num)s days', 1), '1 diena');
    assert.strictEqual(ngettext('%(num)s day', '%(num)s days', 3), '3 dienos');
    assert.strictEqual(ngettext('%(num)s day', '%(num)s days', 11), '11 dienų');
    assert.strictEqual(ngettext('%(num)s thing', '%(num)s things', 5), '5 things');
    """
)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_runtime_semantics():
    runtime = os.path.join(os.path.dirname(__file__), "..", "app", "static", "i18n.js")
    subprocess.run(["node", "-e", RUNTIME_CHECK, runtime], check=True)


LAYOUTS = Path("app/templates")


def test_every_layout_loads_the_catalog():
    """A layout that runs scripts must define gettext() before them."""
    missing = []
    for path in LAYOUTS.rglob("*.html"):
        if "/email" in path.as_posix():
            continue
        text = path.read_text(encoding="utf-8")
        if "<html" not in text or "<script src=" not in text:
            continue
        if "partials/_i18n.html" not in text and "partials/_head.html" not in text:
            missing.append(path.as_posix())
    assert missing == []


def test_login_page_loads_runtime_and_catalog(client):
    html = client.get("/login").get_data(as_text=True)
    assert "i18n.js" in html
    assert "/i18n/en.js?v=" in html


STATIC = Path("app/static")
JS_CALL = re.compile(r"""\bn?gettext\((?:'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)")""")


def test_every_javascript_string_is_extracted():
    """Every gettext() literal in app/static must reach messages.pot.

    Guards the babel.cfg wiring: the javascript mapping, its ignores and the
    repository's extractor (scripts/babel_javascript.py).
    """
    from babel.messages.extract import extract_from_dir

    try:
        from babel.messages.frontend import parse_mapping_cfg
    except ImportError:  # Babel < 2.16
        from babel.messages.frontend import parse_mapping as parse_mapping_cfg

    with open("babel.cfg", encoding="utf-8") as fh:
        method_map, options_map = parse_mapping_cfg(fh)
    # pybabel imports the extractor from the working directory (PYTHONPATH=.);
    # here it is loaded from its file so the test does not depend on sys.path.
    spec = importlib.util.spec_from_file_location("babel_javascript", "scripts/babel_javascript.py")
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    method_map = [
        (pattern, extractor.extract if method == "scripts.babel_javascript:extract" else method)
        for pattern, method in method_map
        if method in ("ignore", "scripts.babel_javascript:extract")
    ]

    def under_static(directory):
        directory = os.path.relpath(directory)
        return directory in ("app", "app/static") or directory.startswith("app/static" + os.sep)

    extracted = set()
    for filename, _lineno, message, _comments, _context in extract_from_dir(
        ".", method_map, options_map, keywords={"gettext": None, "ngettext": (1, 2)}, directory_filter=under_static
    ):
        extracted.add(message if isinstance(message, str) else message[0])
    assert extracted, "nothing extracted: is the javascript mapping in babel.cfg?"

    missing = []
    for path in STATIC.rglob("*.js"):
        parts = path.relative_to(STATIC).parts
        if parts[0] in ("vendor", "dist") or path.name == "i18n.js":
            continue
        source = path.read_text(encoding="utf-8")
        for match in JS_CALL.finditer(source):
            literal = (match.group(1) if match.group(1) is not None else match.group(2))
            literal = literal.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
            if literal not in extracted:
                missing.append(f"{path.as_posix()}:{source.count(chr(10), 0, match.start()) + 1}: {literal}")
    assert missing == []
