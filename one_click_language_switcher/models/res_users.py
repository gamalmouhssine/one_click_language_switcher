# Part of One-Click Language Switcher. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.exceptions import UserError

from .res_config_settings import ALLOWED_CODES_PARAM


class ResUsers(models.Model):
    """Self-service language API used by the navbar language switcher.

    Both methods act exclusively on ``self.env.user``. No user id is ever
    accepted from the client, so a user can neither read nor alter the
    language of somebody else through these endpoints.
    """

    _inherit = "res.users"

    @api.model
    def _one_click_language_allowed_codes(self):
        """Return the language codes an administrator restricted the switcher to.

        An empty set means "no restriction": every active language is offered,
        which is the default and the behaviour of versions before 1.2.0.

        ``ir.config_parameter`` is readable by the system group only, hence the
        sudo(): its scope is one read of one key holding nothing but a list of
        language codes, which every user is allowed to see anyway.

        :rtype: set[str]
        """
        param = self.env["ir.config_parameter"].sudo().get_param(ALLOWED_CODES_PARAM, "")
        return {code.strip() for code in param.split(",") if code.strip()}

    @api.model
    def one_click_language_get_available(self):
        """Return the languages the current user is allowed to switch to.

        Only *active* languages are returned, which in Odoo means the
        languages an administrator has installed and left enabled. The list
        is never hardcoded: it is read from ``res.lang``.

        Reading ``res.lang`` needs no privilege elevation: the access rights
        shipped with ``base`` grant read access on that model to internal
        users, portal users and the public user alike.

        :return: one dict per language, the current language first and the
            remaining ones sorted alphabetically by display name. Each dict
            holds ``code``, ``name``, ``iso_code``, ``direction``, ``active``
            and ``is_current``.
        :rtype: list[dict]
        """
        current_code = self.env.user.lang
        languages = self.env["res.lang"].search([("active", "=", True)])
        allowed = self._one_click_language_allowed_codes()
        if allowed:
            # The language currently in use is always listed, even when an
            # administrator removed it from the offered set: the user has to be
            # able to see which language they are on.
            languages = languages.filtered(
                lambda lang: lang.code in allowed or lang.code == current_code
            )
        entries = [
            {
                "code": lang.code,
                "name": lang.name,
                # ``iso_code`` is optional on res.lang; fall back on the
                # language part of the locale code: ``pt_BR`` and
                # ``sr@latin`` both yield ``pt`` / ``sr``.
                "iso_code": lang.iso_code or lang.code.split("@")[0].split("_")[0],
                "direction": lang.direction,
                "active": True,
                "is_current": lang.code == current_code,
            }
            for lang in languages
        ]
        entries.sort(key=lambda entry: (not entry["is_current"], entry["name"].lower()))
        return entries

    @api.model
    def one_click_language_set(self, lang_code):
        """Set the language of the **currently authenticated** user.

        The target user is always ``self.env.uid``; the caller cannot pass a
        user id. The requested code is validated against ``res.lang`` before
        being written, so only an existing and active language is accepted.

        :param str lang_code: locale code of an active language, e.g. ``fr_FR``.
        :return: ``{"code": ..., "name": ...}`` describing the applied language.
        :rtype: dict
        :raise UserError: if the code is empty, malformed, unknown or inactive.
        """
        if not isinstance(lang_code, str) or not lang_code.strip():
            raise UserError(_("No language was selected."))

        lang = self.env["res.lang"].search(
            [("code", "=", lang_code.strip()), ("active", "=", True)], limit=1
        )
        if not lang:
            raise UserError(
                _("The language %s is not installed or not active.", lang_code.strip())
            )

        allowed = self._one_click_language_allowed_codes()
        user = self.env["res.users"].browse(self.env.uid)
        if allowed and lang.code not in allowed and lang.code != user.lang:
            # Enforced here and not only in the getter: the restriction is a
            # server-side rule, so it cannot be bypassed by crafting an RPC.
            raise UserError(
                _("The language %s is not offered on this database.", lang.code)
            )

        # ``self.env.user`` is a sudo-ed recordset, so browse the record with
        # the caller's own rights instead: ``res.users.write`` recognises a
        # user editing their own record and then only accepts the fields
        # listed in ``SELF_WRITEABLE_FIELDS`` -- ``lang`` is one of them.
        # Writing another user's record from here is therefore impossible,
        # and no explicit sudo() is needed.
        if user.lang != lang.code:
            user.write({"lang": lang.code})
        return {"code": lang.code, "name": lang.name}
