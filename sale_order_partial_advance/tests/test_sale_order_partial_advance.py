# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase
from uuid import uuid4


class TestSaleOrderPartialAdvance(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrderPartialAdvance, cls).setUpClass()

        # MODELS
        cls.so_obj = cls.env['sale.order']
        cls.product_obj = cls.env['product.product']
        cls.account_tax_obj = cls.env['account.tax']
        cls.deposit_product_obj = cls.env['sale.advance.payment.inv']

        # INSTANCES
        cls.partner_id = cls.env['res.partner'].create(
            {'name': '%s' % uuid4()})
        cls.product1 = cls.product_obj.create({
            'name': 'External Hard disk',
            'type':'consu',
            'invoice_policy': 'order',
        })
        cls.product2 = cls.product_obj.create({
            'name': 'Pen drive, SP-2',
            'type': 'consu',
            'invoice_policy': 'order',
        })
        cls.account_tax = cls.account_tax_obj.create(dict(name="Include tax",
                                                      amount='21.00',
                                                      price_include=True))

        # product1 = cls.env.ref('product.product_product_28')
        # product2 = cls.env.ref('product.product_product_29')
        cls.order_lines = [
            (0, 0, {'product_id': cls.product1.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100
                    }),
            (0, 0, {'product_id': cls.product2.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 120
                    })]

        # set default product
        vals = cls.deposit_product_obj._prepare_deposit_product()
        product_id = cls.product_obj.create(vals)
        cls.env['ir.values'].sudo().set_default('sale.config.settings',
                                                 'deposit_product_id_setting',
                                                 product_id.id)
        # set taxes on advance product
        cls.product_advance = cls.deposit_product_obj._default_product_id()
        cls.product_advance.write({'taxes_id': [(6, 0, [cls.account_tax.id])]})

    def test_sale_order_partial_advance(self):
        '''
            Test scenario
            - Create a sale order with 2 lines
            - Confirm the sale order
            - Invoice an advance of 500
            - Invoice the first order line and use 200 from the advance
            - Invoice the balance, the 300 remaining from the initial
              advance should be used automatically
        '''
        # ----------------------------------------------
        # Create and confirm a sale order with 2 lines
        # ----------------------------------------------
        vals = {
            'partner_id': self.partner_id.id,
            'order_line': self.order_lines,
        }
        order = self.so_obj.create(vals)
        self.assertEqual(order.amount_total, 1840.0)
        order.action_confirm()

        context = {"active_model": 'sale.order', "active_ids": [order.id],
                   "active_id": order.id}

        # ----------------------------------------------
        #    Invoice a deposit of 500.0
        #    This create one draft invoice
        # ----------------------------------------------
        adv_wizard = self.env['sale.advance.payment.inv'].with_context(context).create(
            {'advance_payment_method': 'fixed',
             'amount': 500.0,
             })
        adv_wizard.with_context(active_ids=[order.id]).create_invoices()
        self.assertTrue(order.invoice_ids)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 500.0)
        self.assertEqual(order.advance_amount_used, 0.0)
        invoice = order.invoice_ids.filtered(lambda r: r.state == 'draft')
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.amount_total, 500.0)
        self.assertEqual(self.product_advance, invoice.invoice_line_ids.product_id)

        # ---------------------------------------------------------------------
        #    Invoice only one sale order line (with invoice_policy = delivery)
        #    and consume 200.0 from the deposit
        #    result : second draft invoice with 3 lines
        # ---------------------------------------------------------------------
        wizard = self.env['sale.advance.payment.inv'].with_context(context).create({
            'advance_payment_method': 'all',
        })
        self.assertEqual(wizard.advance_amount_available, 500.0)
        wizard.advance_amount_to_use = 200.0
        wizard.with_context(context).create_invoices()
        invoices = order.invoice_ids.filtered(lambda r: r.state == 'draft')
        self.assertEqual(len(invoices), 2)
        inv_adv_line = self.env['account.invoice.line']
        for invoice in invoices:
            for line in invoice.invoice_line_ids:
                if line.product_id == self.product_advance:
                    inv_adv_line = line
                    break

        self.assertEqual(self.account_tax.id,inv_adv_line.invoice_line_tax_ids.id)
        wizard = self.env['sale.advance.payment.inv'].with_context(
            context).create({})

        print '---val---',invoices[0].amount_total
        print '---val---', invoices[1].amount_total
        print '---val---', order.advance_amount
        print '---val---',order.advance_amount_available
        print '---val---',order.advance_amount_used
