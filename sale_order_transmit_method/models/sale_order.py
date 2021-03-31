# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    transmit_method_id = fields.Many2one(
        comodel_name="transmit.method",
        string="Transmission Method",
        track_visibility="onchange",
        ondelete="restrict",
    )

    @api.onchange("partner_id", "company_id")
    def onchange_partner_transmit_method(self):
        self.transmit_method_id = (
            self.partner_id.customer_invoice_transmit_method_id.id or False
        )

    @api.multi
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update({'transmit_method_id': self.transmit_method_id.id})
        return res
