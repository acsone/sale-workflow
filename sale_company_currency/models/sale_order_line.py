# Copyright Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="order_id.company_currency_id",
        string="Company Currency",
        readonly=True,
        store=True,
    )
    price_total_company_currency = fields.Monetary(
        string="Total (company currency)",
        readonly=True,
        compute="_compute_price_total_company_currency",
        currency_field="company_currency_id",
        store=True,
    )
    price_subtotal_company_currency = fields.Monetary(
        string="Subtotal (company currency)",
        readonly=True,
        compute="_compute_price_subtotal_company_currency",
        currency_field="company_currency_id",
        store=True,
    )

    @api.depends("price_total", "order_id.currency_rate")
    def _compute_price_total_company_currency(self):
        for rec in self:
            amount = rec.price_total
            if rec.currency_id != rec.company_id.currency_id:
                amount = amount * rec.order_id.currency_rate
            rec.price_total_company_currency = amount

    @api.depends("price_subtotal", "order_id.currency_rate")
    def _compute_price_subtotal_company_currency(self):
        for rec in self:
            amount = rec.price_subtotal
            if rec.currency_id != rec.company_id.currency_id:
                amount = amount * rec.order_id.currency_rate
            rec.price_subtotal_company_currency = amount
