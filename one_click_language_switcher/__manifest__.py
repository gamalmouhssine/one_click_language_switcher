# Part of One-Click Language Switcher. See LICENSE file for full copyright and licensing details.
{
    "name": "One-Click Language Switcher",
    "summary": "Switch your Odoo language instantly from the backend navbar",
    "description": """
One-Click Language Switcher
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
    "version": "19.0.1.3.2",
    "category": "Productivity",
    "author": "gamalmouhssine",
    "website": "https://github.com/gamalmouhssine/one_click_language_switcher",
    "license": "LGPL-3",
    "price": 19.99,
    "currency": "EUR",
    # ``base_setup`` owns the General Settings form the allow-list is
    # added to. It is a Community module present in every database;
    # no Enterprise dependency is introduced.
    "depends": ["base", "web", "base_setup"],
    "images": [
        "static/description/banner.png",
        "static/description/screenshot_dropdown.png",
        "static/description/screenshot_command_palette.png",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "one_click_language_switcher/static/src/scss/language_switcher.scss",
            "one_click_language_switcher/static/src/js/language_switcher_service.js",
            "one_click_language_switcher/static/src/js/language_switcher.js",
            "one_click_language_switcher/static/src/js/language_commands.js",
            "one_click_language_switcher/static/src/xml/language_switcher.xml",
        ],
    },
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
