# Copyright 2018 Acsone
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date, timedelta

from odoo.tests import common
from odoo import fields


class TestBlanketOrders(common.TransactionCase):

    def test_create_sale_orders(self):
        partner = self.env['res.partner'].create({
            'name': 'TEST',
            'customer': True,
        })
        payment_term = self.env.ref('account.account_payment_term_net')
        product = self.env['product.product'].create({
            'name': 'Demo',
            'categ_id': self.env.ref('product.product_category_1').id,
            'standard_price': 35.0,
            'list_price': 40.0,
            'type': 'consu',
            'uom_id': self.env.ref('product.product_uom_unit').id,
            'default_code': 'PROD_DEL02',
        })
        tomorrow = date.today() + timedelta(days=1)

        blanket_order = self.env['sale.blanket.order'].create({
            'partner_id': partner.id,
            'validity_date': fields.Date.to_string(tomorrow),
            'payment_term_id': payment_term.id,
            'lines_ids': [(0, 0, {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'price_unit': 40.0,
                'original_qty': 20.0,
            })],
        })
        blanket_order.onchange_partner_id()

        self.assertEqual(blanket_order.state, 'draft')

        blanket_order.action_confirm()

        self.assertEqual(blanket_order.state, 'opened')

        wizard1 = self.env['sale.blanket.order.wizard'].with_context(
            active_id=blanket_order.id).create({})
        wizard1.lines_ids[0].write({'qty': 10.0})
        wizard1.create_sale_order()

        wizard2 = self.env['sale.blanket.order.wizard'].with_context(
            active_id=blanket_order.id).create({})
        wizard2.lines_ids[0].write({'qty': 10.0})
        wizard2.create_sale_order()

        self.assertEqual(blanket_order.state, 'expired')
