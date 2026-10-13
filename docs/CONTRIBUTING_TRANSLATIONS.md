# Contributing translations (no Git required)

This project uses **GNU gettext** `.po` files under `translations/<locale>/LC_MESSAGES/messages.po`, compiled at app startup (see [TRANSLATION_SYSTEM.md](TRANSLATION_SYSTEM.md)). You do **not** need Git or developer tools to suggest fixes.

## How we accept help (channels)

Maintainers should pick what fits workload and community size. The **default** for this repository is **A**; scale up to **B** or **C** when needed.

| Channel | Best for | Git? |
|--------|-----------|------|
| **A. GitHub issue (recommended default)** | Wrong/missing wording, one string or a small batch | No — use the “Translation improvement” template when creating an issue |
| **B. Spreadsheet or form** | Many rows at once, non-GitHub users | No — maintainer copies suggestions into `.po` |
| **C. Hosted translation platform** | Ongoing community, many languages, history and glossaries | No for translators; maintainer connects repo or uploads `.po` |

### A. GitHub issue (primary)

1. Open a new issue and choose **Translation improvement**.
2. Fill in language, where you saw the text, current UI text, and your suggested wording.
3. A maintainer updates the correct `messages.po` and merges the change.

No repository access is required.

### B. Spreadsheet or form (optional)

Use when contributors cannot or will not use GitHub:

1. Maintainer shares a table with columns such as: **Language code**, **Screen or page**, **Text as shown now**, **Should be (your suggestion)**, **Notes**.
2. Contributors only edit the suggestion column.
3. Maintainer applies changes to the `.po` files and validates placeholders (see below).

### C. Hosted platform (optional, higher volume)

Examples: [Weblate](https://weblate.org/) (open source, can be self-hosted), [Crowdin](https://crowdin.com/), [POEditor](https://poeditor.com/), [Transifex](https://www.transifex.com/). Translators work in the browser; integration or export/import keeps `.po` in sync with the codebase. Setup is maintainer-owned.

**TimeTracker on Crowdin:** [https://crowdin.com/project/drytrix-timetracker](https://crowdin.com/project/drytrix-timetracker)

#### Crowdin setup (maintainers)

This repo includes a root [`crowdin.yml`](../crowdin.yml) that maps **source** `translations/en/LC_MESSAGES/messages.po` to **translations** under `translations/<locale>/LC_MESSAGES/messages.po`, with **`nb` → `no`** so Norwegian matches `app/config.py` (`no`, not `nb`). You may still have a legacy `translations/nb/` tree locally; prefer **`no`** in Crowdin and in config so you do not maintain two Norwegian copies.

1. **Crowdin account and project** — [Sign up at Crowdin](https://crowdin.com/) if needed. Translators work in **[Drytrix TimeTracker](https://crowdin.com/project/drytrix-timetracker)** (ask a maintainer for access if the project is private). Maintainers configure API tokens and GitHub integration against that same project unless you intentionally use a separate test project.
2. **Source language:** English. Treat the resource as **Gettext PO** (`.po`).
3. **Target languages:** Add every locale you ship: `nl`, `de`, `fr`, `it`, `fi`, `es`, `pt`, `no`, `ar`, `he` (match `LANGUAGES` in `app/config.py`). For Norwegian, add Norwegian (Bokmål) in Crowdin; the `crowdin.yml` mapping writes files into `translations/no/`.
4. **Sync with this repository (pick one):**
   - **GitHub Action:** In the GitHub repo, add Actions secrets `CROWDIN_PROJECT_ID` and `CROWDIN_PERSONAL_TOKEN` (Crowdin project **Details** shows the numeric project ID; **Account Settings → API** creates the token with project access, typically Manager). Run **Crowdin sync** from the **Actions** tab → **Run workflow**. For a **one-time** import of existing `.po` files into Crowdin’s translation memory, temporarily set `upload_translations: true` in [.github/workflows/crowdin-sync.yml](../.github/workflows/crowdin-sync.yml), run it once, then set it back to `false`.
   - **Crowdin’s GitHub integration:** Crowdin → **Integrations → GitHub** → connect the repo and branch; point it at the same `crowdin.yml` so Crowdin can open PRs when translations are updated.
   - **Crowdin CLI:** Install the [Crowdin CLI](https://crowdin.github.io/crowdin-cli/), export the same env vars, run `crowdin upload sources` (and optionally `crowdin upload translations` once) from the repository root.
5. **When developers add or change `_()` strings:** Run `pybabel extract` / `pybabel update` locally (see [TRANSLATION_SYSTEM.md](TRANSLATION_SYSTEM.md)), commit if you version those files, then upload sources to Crowdin again.
6. **Landing translations:** Approve in Crowdin if you use review, then download (workflow or integration PR), merge, and run the app so `.mo` files rebuild.

Translators only need a Crowdin account; they do not use git.

#### Further Crowdin integration (optional)

Pick what reduces manual work without duplicating automation (avoid running **both** the Crowdin GitHub app and the **Crowdin sync** Action on the same events unless you coordinate branches, or you may get competing PRs).

1. **Crowdin → Integrations → GitHub** — Connect the repository and default branch (e.g. `main` or `develop`). Crowdin can open PRs when translations are updated and can watch the repo for changes to configured source files. Use the same [`crowdin.yml`](../crowdin.yml) path the integration expects (usually repo root). This can replace manual Action runs for “download translations” if you prefer Crowdin-driven PRs.
2. **Automate the existing Action** — Extend [.github/workflows/crowdin-sync.yml](../.github/workflows/crowdin-sync.yml) with triggers such as `schedule` (e.g. weekly), or `push` limited to `translations/en/**` and `messages.pot` so new English sources upload shortly after merge. Keep `workflow_dispatch` for on-demand full sync.
3. **Pre-translate and QA** — In the [Drytrix TimeTracker](https://crowdin.com/project/drytrix-timetracker) project, enable **Translation Memory**, **Machine translation** (as a suggestion layer only), and **QA checks** (variables, HTML tags, duplicate translations). Add a **Glossary** for product names and fixed terminology.
4. **Context for translators** — Upload **screenshots** or use Crowdin’s in-context / overlay tools where supported so ambiguous short strings (e.g. “Save”, “Project”) get the right meaning.
5. **Review before merge** — Turn on **proofreading** / “Export only approved” in Crowdin if you want the GitHub Action or integration to pull only reviewed strings (match the Action’s `export_only_approved`-style options to your Crowdin workflow).
6. **CLI in release process** — Add `crowdin upload sources` after `pybabel extract` / `update` in a maintainer script or release checklist so Crowdin always matches the latest POT-derived English catalog.
7. **Notifications** — Slack, email, or webhooks in Crowdin when a language reaches 100% or when there are new strings to translate.

Official references: [Crowdin + GitHub](https://support.crowdin.com/github-integration/), [GitHub Action](https://github.com/crowdin/github-action), [Crowdin CLI](https://crowdin.github.io/crowdin-cli/).

### Other options (reference)

- **Poedit:** Maintainer can zip `translations/<lang>/LC_MESSAGES/messages.po` for a trusted translator; they edit in [Poedit](https://poedit.net/) and send the file back. Avoid two people editing the same locale in parallel without coordination.
- **GitHub web editor on `.po` files:** Possible for experts only; easy to break quoting or plural blocks.

## Rules for translators

Follow these so your suggestion can be applied without breaking the app:

1. **Do not change English source keys.** In `.po` files those are `msgid` lines. In an issue or spreadsheet you describe what you see; maintainers map it to the file. Never invent a new English “key” string.
2. **Preserve placeholders exactly.** If the UI shows `Hello, %(username)s` or similar, your translation must include the same placeholders (same names, same `%(name)s`-style segments). Same for `%s`, `%d`, or other format tokens.
3. **Plurals:** Some strings have one vs many forms. If you are unsure, describe the case in **Notes** and a maintainer will set `msgstr[0]` / `msgstr[1]` correctly in the `.po` file.
4. **Context matters.** Say which **page**, **button**, or **dialog** the text appears on, and attach a **screenshot** if possible. One English phrase can appear in multiple places with different meanings.
5. **Length and tone:** Short labels (buttons, nav) should stay compact. Full sentences can be more natural in your language than literal word-for-word English.

**Supported locale codes** (see `app/config.py` `LANGUAGES`): `en`, `nl`, `de`, `fr`, `it`, `fi`, `es`, `pt`, `no`, `ar`, `he`.

## Maintainer workflow

Designate at least one person responsible for translation intake (issues, spreadsheet, or platform export).

### Syncing catalogs with the codebase

When new or changed `msgid` strings land in the app, refresh every locale from a new template: run **`pybabel extract`** then **`pybabel update`** as in [TRANSLATION_SYSTEM.md](TRANSLATION_SYSTEM.md) (venv with Babel + Jinja2, `babel.cfg` **`[extractors]`** block for Jinja2, root **`messages.pot`** gitignored). Use **`--ignore-obsolete`** if you want obsolete entries removed from all `.po` files after a large refactor.

### Applying contributor suggestions

1. Identify the locale file: `translations/<locale>/LC_MESSAGES/messages.po`.
2. Find the entry (by `msgid` / English source or grep for the current `msgstr`).
3. Update `msgstr` (and plural `msgstr[n]` if needed). Remove `#, fuzzy` if you are sure the translation is correct (fuzzy entries may be ignored at compile time depending on setup).
4. Restart the app or trigger your usual deploy so `.mo` is regenerated (see [TRANSLATION_SYSTEM.md](TRANSLATION_SYSTEM.md) — compilation runs on startup via `app/utils/i18n.py`).

### After new UI strings ship in code

When developers add or change translatable strings:

```bash
PYTHONPATH=. pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
```

Then fill new empty entries in each `messages.po`, run the app, and smoke-test critical screens in a few locales.

### Verification checklist

- [ ] Placeholders in `msgstr` match the `msgid` / source string.
- [ ] `.po` file is valid UTF-8 and parses (Poedit or `msgfmt --check`).
- [ ] UI checked in the target language for overflow or clipping on small screens (especially for short buttons).

## See also

- Technical overview: [TRANSLATION_SYSTEM.md](TRANSLATION_SYSTEM.md)
