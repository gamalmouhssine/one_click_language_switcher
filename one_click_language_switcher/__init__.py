# Part of One-Click Language Switcher. See LICENSE file for full copyright and licensing details.

from . import models

from .models.res_config_settings import ALLOWED_CODES_PARAM


def uninstall_hook(env):
    """Remove the switcher's configuration parameter when the module is removed.

    Odoo drops the module's models and views on its own, but a system
    parameter written at runtime belongs to no XML record and would survive
    the uninstall as an orphan row.
    """
    env["ir.config_parameter"].sudo().search([("key", "=", ALLOWED_CODES_PARAM)]).unlink()
