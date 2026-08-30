# Part of Quick Language Switcher. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

ALLOWED_CODES_PARAM = "quick_language_switcher.allowed_lang_codes"


class ResConfigSettings(models.TransientModel):
    """Let an administrator restrict which languages the switcher offers."""

    _inherit = "res.config.settings"

    quick_language_allowed_lang_ids = fields.Many2many(
        "res.lang",
        string="Languages offered by the switcher",
        domain=[("active", "=", True)],
        help="Languages the Quick Language Switcher offers to users. "
        "Leave empty to offer every active language.",
    )

    def get_values(self):
        """Read the stored codes back into the settings form."""
        res = super().get_values()
        codes = self.env["res.users"]._quick_language_allowed_codes()
        # active_test=False so that a language an administrator allowed and
        # later archived is not silently dropped from the stored selection the
        # next time the settings are saved.
        langs = (
            self.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "in", sorted(codes))])
            if codes
            else self.env["res.lang"].browse()
        )
        res["quick_language_allowed_lang_ids"] = [fields.Command.set(langs.ids)]
        return res

    def set_values(self):
        """Store the selection as a comma separated list of language codes.

        Codes rather than ids are stored so that the setting survives a
        database reload or a language being reinstalled with a new id.
        """
        super().set_values()
        codes = ",".join(sorted(self.quick_language_allowed_lang_ids.mapped("code")))
        # ``ir.config_parameter`` is writable by the system group only, which is
        # already required to reach this form; sudo() only keeps the ORM from
        # re-checking it while saving the settings, as Odoo does for every
        # ``config_parameter`` field.
        self.env["ir.config_parameter"].sudo().set_param(ALLOWED_CODES_PARAM, codes)
