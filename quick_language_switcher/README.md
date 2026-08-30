# Quick Language Switcher

## Overview

Quickly switch the current user's backend language directly from the Odoo
navigation bar. A globe entry is added to the systray: open it, pick a
language, and the web client reloads fully translated. No trip through
**Settings → Users → Preferences** is required, and no administrator rights
are involved.

## Features

* One-click language switching from the navbar
* Dynamically detects the active Odoo languages — no hardcoded language list
* Clear current-language indicator (check mark + screen-reader label)
* Optional Unicode flag with a globe fallback for locales without a country
* Search field appears automatically above ~10 languages
* Command palette entries: <kbd>Ctrl</kbd>+<kbd>K</kbd> then a language name
* Administrators may restrict which languages are offered (General Settings)
* The three most recently used languages are pinned near the top
* RTL friendly (Arabic, Hebrew, …) — Odoo decides the page direction, the addon never forces it
* Responsive: icon only on small screens, icon + language name from `lg` up
* Odoo Community and Odoo Enterprise compatible
* Separate packages for Odoo 17.0, 18.0 and 19.0
* No Enterprise dependency — depends only on `base`, `web` and `base_setup`

## Installation

1. Copy the `quick_language_switcher` directory into one of the directories
   listed in your `addons_path`.
2. Restart the Odoo server.
3. Activate the developer mode, go to **Apps**, click **Update Apps List**.
4. Search for *Quick Language Switcher* and click **Install**.

Command line equivalent:

```bash
./odoo-bin \
  -d my_database \
  --addons-path=addons,custom_addons \
  -i quick_language_switcher \
  --stop-after-init
```

Upgrade:

```bash
./odoo-bin \
  -d my_database \
  --addons-path=addons,custom_addons \
  -u quick_language_switcher \
  --stop-after-init
```

Run the automated tests:

```bash
./odoo-bin \
  -d my_database \
  --addons-path=addons,custom_addons \
  -i quick_language_switcher \
  --test-enable \
  --stop-after-init
```

## Usage

1. Install at least two Odoo languages (**Settings → Translations → Languages**,
   or **Settings → Add Languages**).
2. Install this addon.
3. Open the backend.
4. Click the globe in the top-right navigation bar.
5. Choose a language.
6. The web client reloads in that language.

With a single active language the switcher hides itself: there is nothing to
switch to.

## Compatibility

| Odoo series | Package directory | Manifest version |
| ----------- | ----------------- | ---------------- |
| 17.0        | `17.0/quick_language_switcher/` | `17.0.1.0.0` |
| 18.0        | `18.0/quick_language_switcher/` | `18.0.1.0.0` |
| 19.0        | `19.0/quick_language_switcher/` | `19.0.1.0.0` |

Each package is a standalone addon: install the one matching your Odoo
series. They are **not** interchangeable, because the OWL `Dropdown`
component API changed between 17.0 and 18.0. See `PORTING.md` at the root of the
distribution for the exact list of differences.

Both Community and Enterprise are supported. The addon is written against
Community APIs only, declares no Enterprise dependency, and adds a standard
systray entry, so the Enterprise navbar keeps its own styling.

## Security

The two RPC endpoints live on `res.users` and act **only** on the
authenticated user:

* `quick_language_get_available()` reads active `res.lang` records. Read
  access on `res.lang` is granted to internal and portal users by `base`, so
  no privilege elevation (`sudo()`) is used anywhere in this module.
* `quick_language_set(lang_code)` validates that `lang_code` is a string
  matching an existing **active** language *and* one the administrator allows,
  then writes `lang` on
  `res.users.browse(self.env.uid)`. There is no `user_id` argument, so
  another user's record can never be targeted. The write goes through the
  caller's own rights: Odoo's `res.users.write` recognises a user editing
  their own record and only accepts the fields of `SELF_WRITEABLE_FIELDS`,
  of which `lang` is one.

The allow-list is enforced in `quick_language_set` and not only when building
the list, so a crafted RPC cannot select an excluded language.

An invalid, unknown, inactive or excluded code raises a `UserError`; the client shows a
notification and does **not** reload, so the previous language stays in place.

## Manual test matrix

Only tick a cell after actually running the check on that edition.

| Test             | Odoo 17 CE | Odoo 17 EE | Odoo 18 CE | Odoo 18 EE | Odoo 19 CE | Odoo 19 EE |
| ---------------- | ---------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| Install          | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Navbar rendered  | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Languages loaded | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Switch EN → FR   | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Switch FR → EN   | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Switch EN → AR   | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| RTL after reload | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Mobile           | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Normal user      | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |
| Administrator    | ☐          | ☐          | ☐          | ☐          | ☐          | ☐          |

## Notes and known limitations

* **Flags are cosmetic.** They are derived from the region subtag of the
  locale code (`pt_BR` → 🇧🇷) using Unicode regional indicator symbols; no
  image asset is shipped. Locales without a two-letter region (`ar_001`,
  `sr@latin`, `en`) fall back to a neutral globe icon. Windows renders
  regional indicators as two letters rather than a flag — the switcher stays
  fully usable either way, since the language *name* is always displayed.
* **One RPC per web client session.** The language list is fetched in
  `onWillStart` and cached in the component state. Opening and closing the
  dropdown issues no further request; switching language reloads the client,
  which naturally refreshes the cache.
* **Recent languages** are stored in `localStorage` and hold nothing but
  language codes. Corrupt, disabled or full storage degrades silently to the
  plain alphabetical list.
* **Adding asset files requires a server restart.** Odoo caches each module's
  manifest per process, so a module upgrade alone will not pick up newly
  listed JavaScript or SCSS files.
* See `ROADMAP.md` for the features that were considered and rejected, and why.

## License

LGPL-3. See the `LICENSE` file.
