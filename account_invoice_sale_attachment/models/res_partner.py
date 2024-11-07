# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    allow_invoice_sale_order_attachment = fields.Boolean(
        string="Allow Joining Sale Order Documents",
        default=False,
        help="If enabled, sale order documents will be attached to the invoice email.",
    )

    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()
        return res + ["allow_invoice_sale_order_attachment"]
