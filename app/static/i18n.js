/**
 * gettext for the browser.
 *
 * JavaScript strings are translated the same way as templates and Python code:
 * wrap them in gettext() / ngettext() with the English text as the key, and
 * `pybabel extract` (babel.cfg maps app/static to its JavaScript extractor)
 * puts them in messages.pot next to everything else. /i18n/<locale>.js
 * (app/routes/i18n.py) ships the translated strings as window.i18n.
 *
 *   gettext('Failed to load projects')
 *   gettext('%(count)s characters remaining', { count: n })
 *   ngettext('%(num)s day overdue', '%(num)s days overdue', days)
 *
 * The call mirrors Flask-Babel: %(name)s placeholders are filled from the
 * params object, ngettext() provides %(num)s itself, and a missing
 * translation falls back to the English text, so the strings in the source
 * are always the complete English UI. The catalog is read at call time, not
 * at load time, so this file may run before the catalog script.
 */
(function (global) {
    'use strict';

    function interpolate(text, params) {
        return text.replace(/%\((\w+)\)s|%%/g, function (match, key) {
            if (key === undefined) return '%';
            return Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : match;
        });
    }

    function lookup(msgid) {
        var catalog = global.i18n && global.i18n.catalog;
        return catalog ? catalog[msgid] : undefined;
    }

    function gettext(msgid, params) {
        var translated = lookup(msgid);
        var text = typeof translated === 'string' && translated ? translated : msgid;
        return params ? interpolate(text, params) : text;
    }

    function ngettext(singular, plural, n, params) {
        var forms = lookup(singular);
        var text;
        if (Array.isArray(forms)) {
            text = forms[global.i18n.plural(n)];
        }
        if (!text) {
            text = n == 1 ? singular : plural;
        }
        return interpolate(text, Object.assign({ num: n }, params));
    }

    global.gettext = gettext;
    global.ngettext = ngettext;
})(window);
