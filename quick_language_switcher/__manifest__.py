# Part of Quick Language Switcher. See LICENSE file for full copyright and licensing details.
{
    "name": "Quick Language Switcher",
    "summary": "Switch your Odoo language instantly from the backend navbar",
    "description": """
Quick Language Switcher
=======================

Adds a language selector to the Odoo backend navigation bar so that any
internal user can change *their own* interface language in one click,
without going through Settings > Users > Preferences.

* Languages are read from res.lang: nothing is hardcoded.
* Only active (installed and enabled) languages are offered.
* The server side only ever writes the language of the authenticated user.
* Works on Odoo Community and Odoo Enterprise, no Enterprise dependency.
* Administrators may restrict which languages the switcher offers.
""",
    "version": "18.0.1.3.1",
    "category": "Productivity",
    "author": "gamalmouhssine",
    "website": "https://github.com/gamalmouhssine/quick_language_switcher",
    "license": "LGPL-3",
    # ``base_setup`` owns the General Settings form the allow-list is
    # added to. It is a Community module present in every database;
    # no Enterprise dependency is introduced.
    "depends": ["base", "web", "base_setup"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "quick_language_switcher/static/src/scss/language_switcher.scss",
            "quick_language_switcher/static/src/js/language_switcher_service.js",
            "quick_language_switcher/static/src/js/language_switcher.js",
            "quick_language_switcher/static/src/js/language_commands.js",
            "quick_language_switcher/static/src/xml/language_switcher.xml",
        ],
    },
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
