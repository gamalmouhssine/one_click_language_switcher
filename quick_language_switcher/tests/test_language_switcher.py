# Part of Quick Language Switcher. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.quick_language_switcher import uninstall_hook
from odoo.addons.quick_language_switcher.models.res_config_settings import ALLOWED_CODES_PARAM


@tagged("post_install", "-at_install")
class TestQuickLanguageSwitcher(TransactionCase):
    """Exercise the two RPC endpoints exposed by the module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env["res.users"]
        cls.Lang = cls.env["res.lang"]

        # Work with whatever second language the database already offers and
        # only activate one when there is none: activating a language triggers
        # a full translation load, which is slow and not what is under test.
        active_langs = cls.Lang.search([("active", "=", True)])
        cls.lang_en = active_langs.filtered(lambda lang: lang.code == "en_US")
        second = (active_langs - cls.lang_en)[:1]
        if not second:
            second = cls.Lang._activate_lang("fr_FR")
        cls.lang_second = second
        assert cls.lang_en and cls.lang_second, "at least two languages are required"

        # An inactive language must never be offered nor accepted.
        cls.lang_inactive = cls.Lang.with_context(active_test=False).search(
            [("active", "=", False)], limit=1
        ) or cls.Lang.create(
            {
                "name": "Quick Switcher Inactive",
                "code": "zz_ZY",
                "url_code": "zz_ZY",
                "active": False,
            }
        )

        # Plain internal user: no settings / access rights / technical groups.
        cls.user = cls.Users.create(
            {
                "name": "Quick Switcher Tester",
                "login": "quick_switcher_tester",
                "email": "quick.switcher.tester@example.com",
                "lang": "en_US",
            }
        )
        cls.other_user = cls.Users.create(
            {
                "name": "Quick Switcher Bystander",
                "login": "quick_switcher_bystander",
                "email": "quick.switcher.bystander@example.com",
                "lang": "en_US",
            }
        )

    def _as_user(self):
        """Return the res.users model bound to the plain internal user."""
        return self.Users.with_user(self.user)

    def test_available_returns_only_active_languages(self):
        """The endpoint lists every active language and nothing else."""
        result = self._as_user().quick_language_get_available()

        codes = [entry["code"] for entry in result]
        self.assertIn("en_US", codes)
        self.assertIn(self.lang_second.code, codes)
        self.assertNotIn(self.lang_inactive.code, codes)
        self.assertEqual(len(codes), len(set(codes)), "no duplicated language")

        active_codes = set(self.Lang.search([("active", "=", True)]).mapped("code"))
        self.assertEqual(set(codes), active_codes)

        for entry in result:
            self.assertTrue(entry["active"])
            self.assertTrue(entry["name"])
            self.assertTrue(entry["iso_code"])
            self.assertIn(entry["direction"], ("ltr", "rtl"))

    def test_available_flags_and_sorts_the_current_language_first(self):
        """The current language is flagged and pinned at the top of the list."""
        self.user.lang = self.lang_second.code
        result = self._as_user().quick_language_get_available()

        self.assertEqual(result[0]["code"], self.lang_second.code)
        self.assertTrue(result[0]["is_current"])
        self.assertEqual(
            [entry["is_current"] for entry in result].count(True),
            1,
            "exactly one language is marked as current",
        )
        others = [entry["name"].lower() for entry in result[1:]]
        self.assertEqual(others, sorted(others), "remaining languages are alphabetical")

    def test_user_can_change_their_own_language(self):
        """A plain internal user switches their own language."""
        self.assertEqual(self.user.lang, "en_US")

        result = self._as_user().quick_language_set(self.lang_second.code)

        self.assertEqual(result["code"], self.lang_second.code)
        self.assertEqual(self.user.lang, self.lang_second.code)

    def test_unknown_language_is_rejected(self):
        """A code that does not exist in res.lang is refused."""
        with self.assertRaises(UserError):
            self._as_user().quick_language_set("zz_ZZ")
        self.assertEqual(self.user.lang, "en_US")

    def test_inactive_language_is_rejected(self):
        """An existing but inactive language is refused."""
        with self.assertRaises(UserError):
            self._as_user().quick_language_set(self.lang_inactive.code)
        self.assertEqual(self.user.lang, "en_US")

    def test_empty_or_invalid_input_is_rejected(self):
        """Empty, blank and non-string payloads are refused."""
        for payload in ("", "   ", None, False, 1, [self.lang_second.code]):
            with self.assertRaises(UserError):
                self._as_user().quick_language_set(payload)
        self.assertEqual(self.user.lang, "en_US")

    def test_endpoint_cannot_target_another_user(self):
        """No user id can be injected: only the caller's record is written."""
        self._as_user().quick_language_set(self.lang_second.code)

        self.assertEqual(self.user.lang, self.lang_second.code)
        self.assertEqual(self.other_user.lang, "en_US")

        # The signature accepts a single language code; passing anything else
        # (here a user id) is rejected before any write happens.
        with self.assertRaises(UserError):
            self._as_user().quick_language_set(self.other_user.id)
        self.assertEqual(self.other_user.lang, "en_US")

    def test_plain_user_cannot_write_another_user_language(self):
        """The underlying ORM still refuses cross-user writes."""
        with self.assertRaises(AccessError):
            self.other_user.with_user(self.user).write({"lang": self.lang_second.code})

    def test_other_preferences_are_untouched(self):
        """Switching language only changes `lang`."""
        self.user.write({"tz": "Europe/Brussels", "signature": "<p>Hello</p>"})
        before = self.user.read(["name", "login", "email", "tz", "signature"])[0]

        self._as_user().quick_language_set(self.lang_second.code)

        after = self.user.read(["name", "login", "email", "tz", "signature"])[0]
        self.assertEqual(before, after)
        self.assertEqual(self.user.lang, self.lang_second.code)

    def test_no_administrator_rights_required(self):
        """The tester really is a plain user, without any admin privilege."""
        as_user = self.Users.with_user(self.user)
        self.assertFalse(as_user.browse(self.user.id).has_group("base.group_system"))
        self.assertFalse(as_user.browse(self.user.id).has_group("base.group_erp_manager"))
        self.assertTrue(as_user.browse(self.user.id).has_group("base.group_user"))

        # Both endpoints work with those rights only.
        self.assertTrue(as_user.quick_language_get_available())
        self.assertEqual(
            as_user.quick_language_set(self.lang_second.code)["code"],
            self.lang_second.code,
        )

    def test_switching_to_the_current_language_is_a_no_op(self):
        """Re-selecting the active language succeeds without changing anything."""
        write_date = self.user.write_date
        result = self._as_user().quick_language_set("en_US")

        self.assertEqual(result["code"], "en_US")
        self.assertEqual(self.user.lang, "en_US")
        self.assertEqual(self.user.write_date, write_date)


@tagged("post_install", "-at_install")
class TestQuickLanguageAllowList(TestQuickLanguageSwitcher):
    """The administrator allow-list added in 1.2.0."""

    def _restrict_to(self, *codes):
        self.env["ir.config_parameter"].sudo().set_param(
            ALLOWED_CODES_PARAM, ",".join(codes)
        )

    def test_no_restriction_by_default(self):
        """A fresh database offers every active language."""
        self.assertFalse(self.Users._quick_language_allowed_codes())
        codes = {e["code"] for e in self._as_user().quick_language_get_available()}
        self.assertEqual(codes, set(self.Lang.search([]).mapped("code")))

    def test_restriction_filters_the_offered_languages(self):
        """Only allowed languages are listed."""
        self._restrict_to("en_US")
        codes = [e["code"] for e in self._as_user().quick_language_get_available()]
        self.assertEqual(codes, ["en_US"])
        self.assertNotIn(self.lang_second.code, codes)

    def test_current_language_is_always_listed(self):
        """A user already on a now-excluded language still sees which one it is."""
        self.user.lang = self.lang_second.code
        self._restrict_to("en_US")

        entries = self._as_user().quick_language_get_available()
        codes = [e["code"] for e in entries]
        self.assertIn(self.lang_second.code, codes, "current language kept")
        self.assertIn("en_US", codes)
        self.assertTrue(entries[0]["is_current"])

    def test_restriction_is_enforced_on_write(self):
        """The rule holds server-side: a crafted RPC cannot bypass it."""
        self._restrict_to("en_US")
        with self.assertRaises(UserError):
            self._as_user().quick_language_set(self.lang_second.code)
        self.assertEqual(self.user.lang, "en_US")

    def test_allowed_language_still_switches(self):
        """Languages inside the allow-list keep working."""
        self._restrict_to("en_US", self.lang_second.code)
        self._as_user().quick_language_set(self.lang_second.code)
        self.assertEqual(self.user.lang, self.lang_second.code)

    def test_current_language_may_be_reselected_when_excluded(self):
        """Re-applying the language one already has is never refused."""
        self.user.lang = self.lang_second.code
        self._restrict_to("en_US")
        result = self._as_user().quick_language_set(self.lang_second.code)
        self.assertEqual(result["code"], self.lang_second.code)

    def test_blank_and_padded_codes_are_ignored(self):
        """A sloppily stored parameter does not silently block everything."""
        self.env["ir.config_parameter"].sudo().set_param(
            ALLOWED_CODES_PARAM, f" en_US , , {self.lang_second.code} ,"
        )
        self.assertEqual(
            self.Users._quick_language_allowed_codes(),
            {"en_US", self.lang_second.code},
        )

    def test_settings_round_trip(self):
        """The settings form reads back exactly what it stored."""
        settings = self.env["res.config.settings"].create({})
        settings.quick_language_allowed_lang_ids = self.lang_second
        settings.set_values()

        self.assertEqual(
            self.Users._quick_language_allowed_codes(), {self.lang_second.code}
        )
        values = self.env["res.config.settings"].default_get(
            ["quick_language_allowed_lang_ids"]
        )
        reloaded = self.env["res.config.settings"].new(values)
        # `.new()` yields NewId records, so compare on codes rather than on ids.
        self.assertEqual(
            reloaded.quick_language_allowed_lang_ids.mapped("code"),
            [self.lang_second.code],
        )

    def test_clearing_the_setting_restores_every_language(self):
        """Emptying the selection goes back to offering all active languages."""
        self._restrict_to("en_US")
        settings = self.env["res.config.settings"].create({})
        settings.quick_language_allowed_lang_ids = [(5, 0, 0)]
        settings.set_values()

        self.assertFalse(self.Users._quick_language_allowed_codes())
        codes = {e["code"] for e in self._as_user().quick_language_get_available()}
        self.assertIn(self.lang_second.code, codes)

    def test_plain_user_needs_no_rights_to_read_the_restriction(self):
        """Reading the parameter is sudo-ed, so a normal user is not blocked."""
        self._restrict_to("en_US")
        self.assertEqual(self.Users.with_user(self.user)._quick_language_allowed_codes(), {"en_US"})
        with self.assertRaises(AccessError):
            self.env["ir.config_parameter"].with_user(self.user).search([], limit=1).name

    def test_archived_language_survives_a_settings_save(self):
        """An allowed language that got archived is not silently dropped."""
        self._restrict_to("en_US", self.lang_second.code)
        self.lang_second.active = False
        self.addCleanup(self.lang_second.write, {"active": True})

        settings = self.env["res.config.settings"].create({})
        values = settings.get_values()
        stored = self.env["res.lang"].browse(values["quick_language_allowed_lang_ids"][0][2])
        self.assertIn(self.lang_second, stored, "archived language kept in the form")

    def test_uninstall_hook_removes_the_parameter(self):
        """Uninstalling leaves no orphan configuration row behind."""
        self._restrict_to("en_US")
        Param = self.env["ir.config_parameter"].sudo()
        self.assertTrue(Param.search([("key", "=", ALLOWED_CODES_PARAM)]))

        uninstall_hook(self.env)

        self.assertFalse(Param.search([("key", "=", ALLOWED_CODES_PARAM)]))
        self.assertFalse(self.Users._quick_language_allowed_codes())
