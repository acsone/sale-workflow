# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_amount_available = fields.Float('Advance Available', readonly=True)
    advance_amount_to_use = fields.Float('Advance To Use',
                                         required=True,
                                         default=0.0)

    @api.model
    def default_get(self, fields):
        defaults = super(SaleAdvancePaymentInv, self).default_get(fields)
        order = self.env['sale.order'].browse(
            self.env.context.get('active_ids', []))
        if order:
            defaults['advance_amount_available'] = order.advance_amount_available
        return defaults

    @api.multi
    def create_invoices(self):
        if self.advance_payment_method == 'all':
            ctx = self.env.context.copy()
            ctx['advance_amount_to_use'] = self.advance_amount_to_use
            return super(SaleAdvancePaymentInv, self.with_context(ctx)).create_invoices()
        return super(SaleAdvancePaymentInv, self).create_invoices()
