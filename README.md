# Quick Language Switcher

Change your Odoo back-end language in one click, from the navigation bar.

A globe sits in the systray: open it, pick a language, and the web client
reloads fully translated. No trip through **Settings → Users → Preferences**,
and no administrator rights required — every internal user can change their
own language, and only their own.

![series](https://img.shields.io/badge/Odoo-17.0%20%7C%2018.0%20%7C%2019.0-714B67)
![editions](https://img.shields.io/badge/editions-Community%20%2B%20Enterprise-00c4b4)
![licence](https://img.shields.io/badge/licence-LGPL--3-blue)

![Quick Language Switcher](quick_language_switcher/static/description/banner.png)

![The language dropdown](quick_language_switcher/static/description/screenshot_dropdown.png)

![Command palette](quick_language_switcher/static/description/screenshot_command_palette.png)

## Branches

This repository follows the Odoo Apps convention: **one branch per Odoo
series**, each with the module folder at the root.

| Branch | Odoo series | Module version |
| ------ | ----------- | -------------- |
| [`17.0`](../../tree/17.0) | Odoo 17.0 Community & Enterprise | `17.0.1.3.1` |
| [`18.0`](../../tree/18.0) | Odoo 18.0 Community & Enterprise | `18.0.1.3.1` |
| [`19.0`](../../tree/19.0) | Odoo 19.0 Community & Enterprise | `19.0.1.3.1` |

Check out the branch matching your server; the packages are not
interchangeable, because the OWL `Dropdown` component API changed between
17.0 and 18.0. `PORTING.md` documents every difference between the three.

## Features

* One-click language switching from the navbar
* Command palette entries — <kbd>Ctrl</kbd>+<kbd>K</kbd>, then a language name
* Administrators can restrict which languages are offered (General Settings)
* The three most recently used languages are pinned near the top
* Languages read live from `res.lang` — nothing is hardcoded
* Search field appears automatically above ~10 languages
* RTL friendly (Arabic, Hebrew, …); Odoo decides the page direction
* Responsive: icon only on phones, icon + name from `lg` up
* Community **and** Enterprise; no Enterprise dependency

## Install

```bash
git clone -b 19.0 https://github.com/gamalmouhssine/quick_language_switcher.git
cp -r quick_language_switcher/quick_language_switcher /path/to/custom_addons/
./odoo-bin -d my_db --addons-path=addons,/path/to/custom_addons \
           -i quick_language_switcher --stop-after-init
```

Then open the back end and click the globe. With a single active language the
switcher hides itself — there is nothing to switch to.

> Adding or removing asset files in the manifest requires an Odoo **restart**,
> not just a module upgrade: Odoo caches each manifest per process.

## Security

Two RPC endpoints on `res.users`, both acting only on the authenticated user:

* `quick_language_get_available()` — reads active `res.lang` records.
* `quick_language_set(lang_code)` — validates that the code is a string
  matching an existing, **active** and administrator-allowed language, then
  writes `lang` on `res.users.browse(self.env.uid)`.

There is no `user_id` argument, so another user's record can never be
targeted. The write goes through the caller's own rights: Odoo's
`res.users.write` recognises a user editing their own record and accepts only
the fields in `SELF_WRITEABLE_FIELDS`, of which `lang` is one. The allow-list
is enforced on write and not merely when building the list, so a crafted RPC
cannot select an excluded language.

## Tests

```bash
./odoo-bin -d my_db --addons-path=addons,/path/to/custom_addons \
           -i quick_language_switcher --test-enable \
           --test-tags=/quick_language_switcher --stop-after-init
```

23 backend tests covering the endpoints, the security boundary and the
administrator allow-list.

## Licence

LGPL-3. Independent implementation built on public Odoo APIs; bundles no
third-party code or artwork.
