# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    discount_total = fields.Monetary(
        compute='_compute_discount',
        string='Discount Subtotal',
        readonly=True,
        store=True)
    price_total_no_discount = fields.Monetary(
        compute='_compute_discount',
        string='Subtotal Without Discount',
        readonly=True,
        store=True)

    @api.depends('order_line.discount_total', 'order_line.discount_total')
    def _compute_discount(self):
        for order in self:
            discount_total = sum(order.order_line.mapped('discount_total'))
            price_total_no_discount = sum(
                order.order_line.mapped('price_total_no_discount'))
            order.update({
                'discount_total': discount_total,
                'price_total_no_discount': price_total_no_discount
            })


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    discount_total = fields.Monetary(
        compute='_compute_amount',
        string='Discount Subtotal',
        readonly=True,
        store=True)
    price_total_no_discount = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal Without Discount',
        readonly=True,
        store=True)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        res = super(SaleOrderLine, self)._compute_amount()
        for line in self:
            if not line.discount:
                line.price_total_no_discount = line.price_total
                continue
            price = line.price_unit
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id)

            price_total_no_discount = taxes['total_included']
            discount_total = price_total_no_discount - line.price_total

            line.update({
                'discount_total': discount_total * -1,
                'price_total_no_discount': price_total_no_discount
            })
        return res
