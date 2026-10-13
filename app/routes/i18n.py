"""
Translation catalog for the browser.

``GET /i18n/<locale>.js`` defines ``window.i18n`` for gettext() / ngettext() in
app/static/i18n.js: the locale, its plural rule, and the translations of the
strings that live in JavaScript files. Those are told apart by the ``#:``
location comments pybabel writes into messages.po, so a catalog of thousands of
template strings ships a few hundred to the browser.

The file is built from the .po (the .mo carries no locations), cached per
locale until that file changes, and served with a content hash in its URL, so
browsers cache it until the translations change.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading

from flask import Blueprint, Response, abort, current_app, request, url_for
from flask_babel import get_locale

i18n_bp = Blueprint("i18n", __name__)

#: Source files whose strings belong in the browser catalog, as pybabel records
#: them relative to the repository root.
JS_LOCATION_PREFIX = "app/static/"

#: A gettext plural expression is C syntax that is also valid JavaScript. It is
#: emitted as code, so only the characters that can occur in one get through.
_PLURAL_EXPR = re.compile(r"^[n0-9\s%!=<>&|?:()+\-*/]+$")
_DEFAULT_PLURAL_EXPR = "(n != 1)"

_LOCALE = re.compile(r"^[a-z]{2,3}(_[A-Za-z]{2,4})?$")

_cache: dict[str, tuple[float, str, str]] = {}  # locale -> (.po mtime, etag, body)
_lock = threading.Lock()


def _po_path(locale: str) -> str | None:
    for directory in (current_app.config.get("BABEL_TRANSLATION_DIRECTORIES") or "").split(os.pathsep):
        path = os.path.join(directory, locale, "LC_MESSAGES", "messages.po")
        if directory and os.path.isfile(path):
            return path
    return None


def _build(locale: str, path: str | None) -> tuple[str, str]:
    """Return ``(etag, javascript)`` for one locale from its .po file, if any."""
    from babel.messages.pofile import read_po

    catalog: dict[str, str | list[str]] = {}
    plural_expr = _DEFAULT_PLURAL_EXPR
    if path:
        with open(path, encoding="utf-8") as fh:
            po = read_po(fh, locale=locale)
        if po.plural_expr and _PLURAL_EXPR.match(po.plural_expr):
            plural_expr = po.plural_expr
        for message in po:
            if not message.id or message.fuzzy or not message.string:
                continue
            if not any(location.startswith(JS_LOCATION_PREFIX) for location, _ in message.locations):
                continue
            if isinstance(message.id, tuple):
                if all(message.string):
                    catalog[message.id[0]] = list(message.string)
            else:
                catalog[message.id] = message.string

    body = "window.i18n = {locale: %s, plural: function (n) { return Number(%s); }, catalog: %s};\n" % (
        json.dumps(locale),
        plural_expr,
        # U+2028/2029 are valid JSON but ended string literals in older JavaScript.
        json.dumps(catalog, ensure_ascii=False, sort_keys=True)
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029"),
    )
    etag = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return etag, body


def _get(locale: str) -> tuple[str, str]:
    path = _po_path(locale)
    mtime = os.path.getmtime(path) if path else 0.0
    with _lock:
        cached = _cache.get(locale)
        if cached is None or cached[0] != mtime:
            cached = _cache[locale] = (mtime, *_build(locale, path))
    return cached[1], cached[2]


@i18n_bp.route("/i18n/<locale>.js")
def catalog_js(locale: str):
    if not _LOCALE.match(locale):
        abort(404)
    etag, body = _get(locale)
    if request.if_none_match.contains(etag):
        return Response(status=304, headers={"ETag": etag})
    response = Response(body, mimetype="application/javascript")
    response.headers["ETag"] = etag
    # The URL from i18n_catalog_url() carries the hash, so that one can be cached
    # for good; any other URL must revalidate.
    if request.args.get("v") == etag:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers["Cache-Control"] = "no-cache"
    return response


@i18n_bp.app_template_global()
def i18n_catalog_url() -> str:
    """URL of the current locale's catalog script, hashed for caching."""
    locale = str(get_locale() or current_app.config.get("BABEL_DEFAULT_LOCALE", "en"))
    etag, _ = _get(locale)
    return url_for("i18n.catalog_js", locale=locale, v=etag)
