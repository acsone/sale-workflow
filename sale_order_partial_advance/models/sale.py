# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.depends('invoice_ids')
    def _compute_advance_amounts(self):
        advance_amount = 0
        advance_amount_used = 0
        adv_product_id =\
            self.env['sale.advance.payment.inv']._default_product_id()
        for invoice in self.invoice_ids:
            if invoice.state == 'cancel' or invoice.cancelled_by_refund:
                continue
            advance_amount += sum([line.price_unit
                                  for line in invoice.invoice_line_ids
                                  if (line.product_id == adv_product_id and
                                      line.price_unit > 0)])
            advance_amount_used -= sum([line.price_unit
                                        for line in invoice.invoice_line_ids
                                        if (line.product_id ==
                                            adv_product_id and
                                            line.price_unit < 0)])
        self.advance_amount_available = advance_amount - advance_amount_used
        self.advance_amount = advance_amount
        self.advance_amount_used = advance_amount_used

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res_id = super(SaleOrder, self).action_invoice_create(grouped, final)
        # see how to update invoice line
        invoice_obj = self.env['account.invoice'].browse(res_id)
        for line in invoice_obj.invoice_line_ids:
            if self.env.context.get('advance_amount_to_use'):
                line.write({'price_unit': - self.env.context.get('advance_amount_to_use')})
        return res_id

    """@api.model
    def _prepare_invoice(self):
        adv_product_id =\
            self.env['sale.advance.payment.inv']._default_product_id()
        adv_line_count = 0
        for invoice_line in self.invoice_ids.invoice_line_ids:
            if invoice_line.product_id == adv_product_id:
                if adv_line_count == 0 and self.advance_amount_available > 0:
                    invoice_line.write(
                        {'price_unit': - self.advance_amount_available})
                    adv_line_count += 1
                else:
                    self.remove(invoice_line.id)
                    invoice_line.unlink()
        return super(SaleOrder, self)._prepare_invoice()"""

    advance_amount = fields.Float('Advance Amount',
                                  compute='_compute_advance_amounts')
    advance_amount_available = fields.Float('Advance Available',
                                            compute='_compute_advance_amounts')
    advance_amount_used = fields.Float('Advance Used',
                                       compute='_compute_advance_amounts')
