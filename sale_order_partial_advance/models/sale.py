# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.depends('invoice_ids')
    def _compute_advance_amounts(self):
        advance_amount, advance_amount_used = 0, 0
        adv_product_id =\
            self.env['sale.advance.payment.inv']._default_product_id()
        for invoice in self.invoice_ids:
            if invoice.state == 'cancel' or invoice.cancelled_by_refund:
                continue
            advance_amount += sum([line.price_unit
                                  for line in invoice.invoice_line
                                  if (line.product_id.id == adv_product_id and
                                      line.price_unit > 0)])
            advance_amount_used -= sum([line.price_unit
                                        for line in invoice.invoice_line
                                        if (line.product_id.id ==
                                            adv_product_id and
                                            line.price_unit < 0)])
        self.advance_amount_available = advance_amount - advance_amount_used
        self.advance_amount = advance_amount
        self.advance_amount_used = advance_amount_used

    @api.model
    def _prepare_invoice(self, order, lines):
        adv_product_id =\
            self.env['sale.advance.payment.inv']._get_advance_product()
        adv_line_count = 0
        for invoice_line in self.env['account.invoice.line'].browse(lines):
            if invoice_line.product_id.id == adv_product_id:
                if adv_line_count == 0 and order.advance_amount_available > 0:
                    invoice_line.write(
                        {'price_unit': - order.advance_amount_available})
                    adv_line_count += 1
                else:
                    lines.remove(invoice_line.id)
                    invoice_line.unlink()
        return super(SaleOrder, self)._prepare_invoice(order, lines)

    advance_amount = fields.Float('Advance Amount',
                                  compute='_compute_advance_amounts')
    advance_amount_available = fields.Float('Advance Available',
                                            compute='_compute_advance_amounts')
    advance_amount_used = fields.Float('Advance Used',
                                       compute='_compute_advance_amounts')
