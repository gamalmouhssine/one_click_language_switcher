# Quick Language Switcher — roadmap

Status of every feature considered after v1.0.0. Each entry records what it is,
why it is (or is not) worth building, and how it was verified.

| # | Feature | Effort | Status |
| - | ------- | ------ | ------ |
| 1 | Command palette entries | S | ✅ Done — v1.1.0 |
| 2 | Administrator allow-list of offered languages | M | ✅ Done — v1.2.0 |
| 3 | Recently used languages | S | ✅ Done — v1.3.0 |
| 4 | Burger-menu entry for phones | M | ❌ Rejected — already covered |
| 5 | Country-flag images instead of emoji | S | ❌ Rejected — assets do not exist |
| 6 | Switch language without reloading | L | ❌ Rejected — not achievable cleanly |
| 7 | Portal / website language switcher | L | ❌ Out of scope |

---

## 1. Command palette entries — done in 1.1.0

Type <kbd>Ctrl</kbd>+<kbd>K</kbd> and then a language name to switch directly,
without opening the dropdown. One entry is offered per language other than the
current one.

**Why.** It is the fastest possible path to the feature, it costs no screen
space, and it makes the module usable for people who never take their hands off
the keyboard. Odoo's own `SwitchCompanyMenu` registers a palette command for
the same reason.

**How.** A provider in `registry.category("command_provider")`. The registry,
the `{ provide(env, options) }` shape and the awaiting of asynchronous
providers (`Promise.all` in `command_palette.js`) are identical in 17.0, 18.0
and 19.0, so this file is shared verbatim by the three packages.

**Consequence.** The language list and the switch logic moved out of the OWL
component into a small service (`quick_language_switcher` in the `services`
registry), so the systray dropdown and the palette share one cached fetch
instead of issuing two RPCs.

## 2. Administrator allow-list — done in 1.2.0

Settings → General Settings → *Quick Language Switcher* lets an administrator
choose which of the installed languages the switcher offers. Empty selection
(the default) means "offer them all", so behaviour is unchanged on upgrade.

**Why.** The single most requested thing once a database has fifteen languages
installed for translation purposes but should only offer four to its users.
It is what separates a utility from something worth publishing.

**How.** `res.config.settings` writing an `ir.config_parameter`
(`quick_language_switcher.allowed_lang_codes`), read back and applied inside
`quick_language_get_available` *and* enforced in `quick_language_set` — the
restriction is a server-side rule, not a display filter, so it cannot be
bypassed by crafting an RPC.

**Cost.** Adds `base_setup` to `depends`, because that is the module owning the
General Settings form. `base_setup` is Community, LGPL-3 and present in every
Odoo database; no Enterprise dependency is introduced.

## 3. Recently used languages — done in 1.3.0

The last three languages picked on this browser are pinned directly under the
current one, above the rest of the alphabetical list.

**Why.** Cheap, and it removes the search step for the bilingual and trilingual
users who are the actual audience of this module.

**How.** `browser.localStorage` through `@web/core/browser/browser`, so it stays
mockable and never touches `window` directly. Stores nothing but language
codes. Reads are defensive: corrupt or absent data degrades to the plain
alphabetical list.

## 4. Burger-menu entry for phones — rejected

**Considered:** adding an entry to `registry.category("user_menuitems")` so the
switcher shows up in the mobile burger menu next to the other preferences.

**Rejected because it is already covered.** The systray component deliberately
carries no `d-none d-md-block`, unlike Odoo's own user and company menus, so
the globe already renders at every viewport width; only the language *label* is
hidden below `lg`. A burger entry would duplicate the same feature in a second
place, and because burger items are flat clickable rows it would additionally
need a Dialog to host the list. More surface, more cross-version risk, no gain.

## 5. Country-flag images instead of emoji — rejected

**Considered:** using `res.lang.flag_image_url`, which exists in 17.0, 18.0 and
19.0, to render real flag images and side-step the fact that Windows renders
regional-indicator pairs as two letters rather than a flag.

**Rejected because the images are not there.** That computed field falls back to
`/base/static/img/country_flags/<cc>.png`, and the `country_flags` directory
does not exist in Community 17.0, 18.0 or 19.0 — every such URL 404s unless an
administrator has uploaded a `flag_image` by hand. It would trade "two letters
on Windows" for "broken-image icon on every platform". Shipping flag artwork
ourselves was excluded from the start for licensing reasons.

## 6. Switching without a page reload — rejected

Server-rendered strings — view labels, field strings, selection values, action
names — are all resolved from the request context. There is no supported way to
swap them in place; every approach leaves part of the interface in the old
language. The reload is the correct behaviour, not a shortcut, and it is what
Odoo's own preferences dialog does (`reload_context`).

## 7. Portal / website switcher — out of scope

A different product with different constraints, and `website` already ships its
own language selector for public pages. The module targets authenticated
back-end users, as stated in the README.

---

## Verification

Every feature above was tested before being marked done.

* **Backend** — 21 automated tests (`tests/test_language_switcher.py`), run on a
  clean Odoo 19.0 database: 21/21 pass. Ten of them cover the allow-list,
  including that it is enforced on write and not merely when listing.
* **JavaScript** — 25 assertions run against each of the three packages with the
  `@web/*` modules stubbed: 14 for the service and the command provider
  (single cached fetch, concurrent-switch guard, failure path, provider
  contents and actions) and 11 for the recent-languages history (ordering,
  three-entry cap, no duplicates, corrupt/disabled/full storage).
* **Templates** — compiled *and* rendered against the `owl.js` runtime shipped
  by each branch, with the real `Dropdown` prop schemas and OWL validation on.
* **Live** — installed on Odoo 19.0 Community: the service, provider and
  history all appear in the served `web.assets_backend` bundle, the allow-list
  field renders inside General Settings, and a crafted RPC for an excluded
  language is refused.

---

## Not planned

* **Per-company language memory** (remember a language per active company) —
  interesting for multi-company groups, but the interaction with company
  switching is subtle and the audience is small.
* **Audit log of language changes** — a user changing their own display
  language is not a security-relevant event.
* **Hiding the switcher per user group** — an administrator who wants that can
  uninstall the module; a group check would add an access-rights surface for
  very little benefit.
