# One-Click Language Switcher — differences between the 17.0, 18.0 and 19.0 packages

Everything in this module is shared between the three Odoo series except the
points listed below. Each package targets the **native API of its own release**;
there is no runtime version detection anywhere in the code
(no `odoo.info.server_version` checks, no `try { import }` tricks).

Baseline for this document: the **19.0** package.

---

## Summary

| File                                    | 17.0 vs 19.0 | 18.0 vs 19.0 |
| --------------------------------------- | ------------ | ------------ |
| `__init__.py`                            | identical    | identical    |
| `__manifest__.py`                        | version only | version only |
| `models/__init__.py`                     | identical    | identical    |
| `models/res_users.py`                    | 1 line       | identical    |
| `tests/__init__.py`                      | identical    | identical    |
| `tests/test_language_switcher.py`        | identical    | identical    |
| `static/src/scss/language_switcher.scss` | identical    | identical    |
| `static/src/js/language_switcher.js`     | 3 hunks      | identical    |
| `static/src/js/language_switcher_service.js` | identical | identical |
| `static/src/js/language_commands.js`     | identical    | identical    |
| `models/res_config_settings.py`          | identical    | identical    |
| `views/res_config_settings_views.xml`    | identical    | identical    |
| `static/src/xml/language_switcher.xml`   | rewritten    | identical    |
| `static/description/*`, `README.md`      | identical    | identical    |
| `i18n/one_click_language_switcher.pot`       | header only  | header only  |

**18.0 and 19.0 are byte-identical apart from the manifest `version` string.**
Every other difference below concerns 17.0 only.

---

## 1. `__manifest__.py` — all three packages

Only the `version` key changes, as required by the Odoo Apps store:

```
"version": "17.0.1.0.0"     # 17.0 package
"version": "18.0.1.0.0"     # 18.0 package
"version": "19.0.1.0.0"     # 19.0 package
```

`depends`, `assets` and the `web.assets_backend` bundle name are valid and
unchanged across 17.0 → 19.0.

## 2. `models/res_users.py` — 17.0 only

`@api.readonly` does not exist in Odoo 17.0 (it was introduced with the
read-only-replica support in 18.0, implemented in `odoo/api.py` there and in
`odoo/orm/decorators.py` in 19.0). The 17.0 package therefore drops that one
decorator from `quick_language_get_available`:

```diff
     @api.model
-    @api.readonly
     def quick_language_get_available(self):
```

Everything else in the model is byte-identical, because the relevant server
APIs did not change between 17.0 and 19.0:

* `res.lang` still exposes `code`, `name`, `iso_code`, `direction` and `active`.
* `res.users.SELF_WRITEABLE_FIELDS` still contains `lang`, and
  `res.users.write` still escalates a user's write on their own record when
  every written key is self-writeable — identical code in 17.0, 18.0 and 19.0.
* `env.user` is still a sudo-ed recordset in all three, which is why the module
  browses `self.env.uid` explicitly instead of writing on `self.env.user`.

## 3. `static/src/js/language_switcher.js` — 17.0 only

### 3.1 Module annotation

Odoo 17.0 still requires the `/** @odoo-module **/` banner for files under
`static/src`; 18.0 made it implicit.

```diff
+/** @odoo-module **/
+
 import { Component, onWillStart, useRef, useState } from "@odoo/owl";
```

### 3.2 `DropdownGroup` does not exist in 17.0

`@web/core/dropdown/dropdown_group` was added in 18.0. In 17.0 dropdowns
coordinate through the global `Dropdown.bus`, so no grouping component is
imported or rendered:

```diff
-import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
...
-    static components = { Dropdown, DropdownGroup, DropdownItem };
+    static components = { Dropdown, DropdownItem };
```

### 3.3 Dropdown open callback

18.0/19.0 expose `onStateChanged(isOpen)`; 17.0 exposes `onOpened()` (and a
differently shaped `onStateChanged` that receives a state object). The 17.0
package uses the callback native to that release:

```diff
-    onDropdownStateChanged(isOpen) {
-        if (isOpen) {
-            this.state.search = "";
-            this.searchInputRef.el?.focus();
-        }
-    }
+    onDropdownOpened() {
+        this.state.search = "";
+        if (this.searchInputRef.el) {
+            this.searchInputRef.el.focus();
+        }
+    }
```

### 3.4 What is *not* different

`registry.category("systray")`, `useService("orm")`,
`useService("notification")`, `_t` from `@web/core/l10n/translation`,
`browser` from `@web/core/browser/browser` and the OWL hooks used here all
have the same import paths and semantics in 17.0, 18.0 and 19.0. The systray
registry entry shape (`{ Component }` plus a `sequence`) is also unchanged.

The module deliberately does **not** use the frontend user service, because
its API changed (`useService("user")` in 17.0 → `import { user } from
"@web/core/user"` in 18.0/19.0, and `user.lang` switched from the Python
locale format `en_US` to the JS format `en-US`). The current language is taken
from the server payload's `is_current` flag instead, which is both the
authoritative source (`res.users.lang`) and version-neutral.

## 4. `static/src/xml/language_switcher.xml` — 17.0 only

The OWL `Dropdown` component was rewritten between 17.0 and 18.0; the template
is the only file that had to be genuinely re-authored.

| Concern           | 17.0                                     | 18.0 / 19.0                                    |
| ----------------- | ---------------------------------------- | ---------------------------------------------- |
| Toggle content    | `<t t-set-slot="toggler">`               | first child element (a plain `<button>`)       |
| Menu content      | default slot                             | `<t t-set-slot="content">`                     |
| Root element      | `Dropdown` renders `div.o-dropdown`      | you render your own wrapper `<div>`            |
| Root CSS class    | `class="'…'"` prop                       | class on your own wrapper                      |
| Toggle CSS class  | `togglerClass="'…'"` prop                | class on your own `<button>`                   |
| Accessible name   | `title="…"` prop + visually-hidden span  | `t-att-title` / `t-att-aria-label` on the button |
| Grouping          | implicit (`Dropdown.bus`)                | `<DropdownGroup group="'web-navbar-group'">`   |
| Item attributes   | `dataset="{ langCode: … }"`              | `attrs="{ 'data-lang-code': …, 'aria-current': … }"` |
| Item closing mode | `parentClosingMode` (unused, default ok) | `closingMode` (unused, default ok)             |
| Keyboard nav hint | n/a                                      | `o-navigable` class on the search input        |

`menuClass`, `position` and `disabled` are props of `Dropdown` in all three
releases and are used identically.

Because 17.0's `DropdownItem` has no generic `attrs` prop, the 17.0 template
cannot set `aria-current` on the item. The current language is still conveyed
without relying on colour: a `fa-check` icon plus a `visually-hidden`
"Current language" label, which is present in every package.

## 4b. Features added after 1.0.0

Nothing in the command palette provider, the shared service, the recent
languages history or the administrator allow-list needed version-specific
code:

* `registry.category("command_provider")`, the `{ provide(env, options) }`
  shape and the awaiting of asynchronous providers are identical in the three
  releases, as is `_t("...%s", value)` substitution.
* `registry.category("services")` and `browser.localStorage` from
  `@web/core/browser/browser` are unchanged.
* `base_setup.res_config_settings_view_form` exposes the same
  `//block[@name='languages_setting_container']` anchor in 17.0, 18.0 and
  19.0, so one settings view inherit serves all three.

## 5. `i18n/one_click_language_switcher.pot`

Same entries in all three packages; only the `Project-Id-Version` header
mentions the matching Odoo series. The template was produced with Odoo's own
extractor (`odoo-bin i18n export -l pot`), which is why all six JavaScript
strings are routed through `_t()` in the component rather than written as raw
text in the OWL template.

---

## Frontend automated tests

No QUnit/HOOT test is shipped. The web test frameworks are not comparable
across the three targets — 17.0 ships QUnit only (`addons/web/static/lib/hoot`
does not exist on that branch), 18.0 introduced HOOT alongside QUnit, and 19.0
has moved its own web suite onto HOOT with different mounting helpers. A
shared frontend test would have to be written three times against three
unrelated APIs and would break on every minor release, which is exactly the
fragility the specification asks to avoid.

The backend endpoints — where all validation and all security live — are
covered by 11 automated tests that run identically on the three series
(`tests/test_language_switcher.py`). The UI behaviour is covered by the manual
test matrix in `README.md`.
