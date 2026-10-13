/**
 * Inline edit for duration and notes on time entries overview table.
 */
(function () {
  'use strict';

  var activeEditor = null;

  function getNotesRaw(td) {
    var raw = td.getAttribute('data-notes-raw');
    if (raw == null || raw === '') return '';
    try {
      return JSON.parse(raw);
    } catch (e) {
      return raw;
    }
  }

  function setNotesRaw(td, text) {
    td.setAttribute('data-notes-raw', JSON.stringify(text == null ? '' : String(text)));
  }

  function stripTruncate(s, maxLen) {
    var d = document.createElement('div');
    d.textContent = s || '';
    var t = (d.textContent || '').trim();
    if (!t) return '-';
    if (t.length <= maxLen) return t;
    return t.slice(0, maxLen);
  }

  function parseDurationToSeconds(str) {
    str = (str || '').trim();
    if (!str) return NaN;
    if (/^\d+(\.\d+)?$/.test(str)) {
      return Math.round(parseFloat(str) * 3600);
    }
    var parts = str.split(':').map(function (p) {
      return parseInt(p, 10);
    });
    if (parts.some(function (x) { return isNaN(x); })) return NaN;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 3600 + parts[1] * 60;
    return NaN;
  }

  function parseLocalParts(isoLocal) {
    if (!isoLocal || typeof isoLocal !== 'string') return null;
    var m = isoLocal.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
    if (!m) return null;
    return {
      y: parseInt(m[1], 10),
      mo: parseInt(m[2], 10) - 1,
      d: parseInt(m[3], 10),
      h: parseInt(m[4], 10),
      mi: parseInt(m[5], 10),
    };
  }

  function formatLocalDatetime(d) {
    function pad(n) {
      return String(n).padStart(2, '0');
    }
    return (
      d.getFullYear() +
      '-' +
      pad(d.getMonth() + 1) +
      '-' +
      pad(d.getDate()) +
      'T' +
      pad(d.getHours()) +
      ':' +
      pad(d.getMinutes())
    );
  }

  function isoToLocalDatetimeLocal(iso) {
    if (!iso || typeof iso !== 'string') return '';
    var d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    return formatLocalDatetime(d);
  }

  function flashOk(cell) {
    var span = document.createElement('span');
    span.className = 'time-entry-inline-ok ml-1 inline-block text-emerald-600 dark:text-emerald-400';
    span.setAttribute('aria-hidden', 'true');
    span.textContent = '\u2713';
    span.style.opacity = '0';
    span.style.transition = 'opacity 0.2s ease';
    cell.appendChild(span);
    requestAnimationFrame(function () {
      span.style.opacity = '1';
    });
    setTimeout(function () {
      span.style.opacity = '0';
      setTimeout(function () {
        if (span.parentNode) span.parentNode.removeChild(span);
      }, 200);
    }, 450);
  }

  function toastError(msg) {
    if (window.toastManager && typeof window.toastManager.error === 'function') {
      window.toastManager.error(msg || gettext('Error'), gettext('Error'), 4000);
    } else {
      alert(msg || gettext('Error'));
    }
  }

  function restoreNotesButton(td, displayText, notesFull) {
    setNotesRaw(td, notesFull);
    td.innerHTML =
      '<button type="button" class="time-entry-inline-target inline-flex max-w-full cursor-pointer rounded border border-transparent px-1 py-0.5 text-left hover:border-border-light hover:bg-background-light dark:hover:border-border-dark dark:hover:bg-background-dark" data-inline-field="notes" tabindex="0" title="">' +
      '<span class="time-entry-inline-display block max-w-xs truncate"></span></button>';
    var btn = td.querySelector('button');
    if (btn) btn.setAttribute('title', gettext('Click to edit'));
    var disp = td.querySelector('.time-entry-inline-display');
    if (disp) disp.textContent = displayText;
  }

  function restoreDurationButton(td, formatted) {
    var durCell = td;
    durCell.querySelectorAll('.time-entry-inline-ok').forEach(function (n) { n.remove(); });
    durCell.innerHTML =
      '<button type="button" class="time-entry-inline-target inline-flex max-w-full cursor-pointer rounded border border-transparent px-1 py-0.5 text-left hover:border-border-light hover:bg-background-light dark:hover:border-border-dark dark:hover:bg-background-dark" data-inline-field="duration" tabindex="0" title="">' +
      '<span class="time-entry-inline-display"></span></button>';
    var btn = durCell.querySelector('button');
    if (btn) btn.setAttribute('title', gettext('Click to edit'));
    var disp = durCell.querySelector('.time-entry-inline-display');
    if (disp) disp.textContent = formatted;
  }

  function finishNotesEdit(td, textarea, entryId, originalNotes, originalDisplay) {
    var next = (textarea.value || '').trim();
    if (next === String(originalNotes || '').trim()) {
      restoreNotesButton(td, originalDisplay, originalNotes);
      activeEditor = null;
      return;
    }
    fetch('/api/entry/' + encodeURIComponent(entryId), {
      method: 'PUT',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: next }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { res: res, data: data };
        });
      })
      .then(function (_ref) {
        var res = _ref.res;
        var data = _ref.data;
        if (!res.ok) {
          throw new Error((data && data.error) || res.statusText);
        }
        var ent = data.entry || {};
        var notesVal = ent.notes != null ? ent.notes : next;
        restoreNotesButton(td, stripTruncate(notesVal, 60), notesVal);
        flashOk(td);
        activeEditor = null;
      })
      .catch(function (err) {
        toastError(err.message || gettext('Could not save notes'));
        restoreNotesButton(td, originalDisplay, originalNotes);
        activeEditor = null;
      });
  }

  function finishDurationEdit(td, input, entryId, originalFormatted, meta) {
    var secs = parseDurationToSeconds(input.value);
    if (isNaN(secs) || secs < 0) {
      toastError(gettext('Invalid duration'));
      restoreDurationButton(td, originalFormatted);
      activeEditor = null;
      return;
    }
    var parts = parseLocalParts(meta.startLocal);
    if (!parts) {
      toastError(gettext('Missing start time'));
      restoreDurationButton(td, originalFormatted);
      activeEditor = null;
      return;
    }
    var startDate = new Date(parts.y, parts.mo, parts.d, parts.h, parts.mi, 0, 0);
    var breakSec = parseInt(meta.breakSeconds, 10) || 0;
    var endMs = startDate.getTime() + (secs + breakSec) * 1000;
    var endDate = new Date(endMs);
    var endStr = formatLocalDatetime(endDate);
    fetch('/api/entry/' + encodeURIComponent(entryId), {
      method: 'PUT',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ end_time: endStr }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { res: res, data: data };
        });
      })
      .then(function (_ref2) {
        var res = _ref2.res;
        var data = _ref2.data;
        if (!res.ok) {
          throw new Error((data && data.error) || res.statusText);
        }
        var ent = data.entry || {};
        var df = ent.duration_formatted != null ? ent.duration_formatted : input.value.trim();
        td.setAttribute('data-duration-formatted', df);
        if (ent.duration_seconds != null) td.setAttribute('data-duration-seconds', String(ent.duration_seconds));
        if (ent.end_time) {
          td.setAttribute('data-end-local', isoToLocalDatetimeLocal(ent.end_time));
        }
        restoreDurationButton(td, df);
        flashOk(td);
        activeEditor = null;
      })
      .catch(function (err) {
        toastError(err.message || gettext('Could not save duration'));
        restoreDurationButton(td, originalFormatted);
        activeEditor = null;
      });
  }

  function openNotesEditor(btn) {
    if (activeEditor) return;
    var td = btn.closest('td[data-notes-cell]');
    if (!td) return;
    var tr = td.closest('tr[data-entry-id]');
    if (!tr) return;
    var entryId = tr.getAttribute('data-entry-id');
    var originalNotes = String(getNotesRaw(td) || '');
    var disp = btn.querySelector('.time-entry-inline-display');
    var originalDisplay = disp ? disp.textContent : '-';
    activeEditor = { type: 'notes', td: td };
    var ta = document.createElement('textarea');
    ta.className = 'form-input w-full max-w-xs text-sm';
    ta.rows = 4;
    ta.value = originalNotes;
    td.innerHTML = '';
    td.appendChild(ta);
    ta.focus();
    ta.select();
    ta.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        ta.removeEventListener('blur', onBlur);
        finishNotesEdit(td, ta, entryId, originalNotes, originalDisplay);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        ta.removeEventListener('blur', onBlur);
        restoreNotesButton(td, originalDisplay, originalNotes);
        activeEditor = null;
      }
    });
    function onBlur() {
      setTimeout(function () {
        if (activeEditor && activeEditor.td === td) {
          finishNotesEdit(td, ta, entryId, originalNotes, originalDisplay);
        }
      }, 0);
    }
    ta.addEventListener('blur', onBlur);
  }

  function openDurationEditor(btn) {
    if (activeEditor) return;
    var td = btn.closest('td[data-duration-cell]');
    if (!td) return;
    if (td.getAttribute('data-can-edit-duration') !== '1') return;
    var tr = td.closest('tr[data-entry-id]');
    if (!tr) return;
    var entryId = tr.getAttribute('data-entry-id');
    var originalFormatted = td.getAttribute('data-duration-formatted') || '';
    var meta = {
      startLocal: td.getAttribute('data-start-local') || '',
      breakSeconds: td.getAttribute('data-break-seconds') || '0',
    };
    activeEditor = { type: 'duration', td: td };
    var inp = document.createElement('input');
    inp.type = 'text';
    inp.className = 'form-input w-28 text-sm';
    inp.value = originalFormatted;
    td.innerHTML = '';
    td.appendChild(inp);
    inp.focus();
    inp.select();
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        inp.removeEventListener('blur', onBlurDur);
        finishDurationEdit(td, inp, entryId, originalFormatted, meta);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        inp.removeEventListener('blur', onBlurDur);
        restoreDurationButton(td, originalFormatted);
        activeEditor = null;
      }
    });
    function onBlurDur() {
      setTimeout(function () {
        if (activeEditor && activeEditor.td === td) {
          finishDurationEdit(td, inp, entryId, originalFormatted, meta);
        }
      }, 0);
    }
    inp.addEventListener('blur', onBlurDur);
  }

  function onClick(e) {
    var btn = e.target.closest('[data-inline-field]');
    if (!btn || !e.currentTarget.contains(btn)) return;
    if (btn.closest('a')) return;
    var field = btn.getAttribute('data-inline-field');
    if (field === 'notes') openNotesEditor(btn);
    else if (field === 'duration') openDurationEditor(btn);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var root = document.getElementById('timeEntriesListContainer');
    if (!root) return;
    root.addEventListener('click', onClick);
  });
})();
