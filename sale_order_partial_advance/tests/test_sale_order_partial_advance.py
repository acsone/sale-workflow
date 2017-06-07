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

        # INSTANCES
        cls.partner_id = cls.env['res.partner'].create(
            {'name': '%s' % uuid4()})
        cls.product1 = cls.product_obj.create({
            'name': 'External Hard disk',
            'type':'consu',
        })
        cls.product2 = cls.product_obj.create({
            'name': 'Pen drive, SP-2',
            'type': 'consu'
        })
        cls.account_tax = cls.account_tax_obj.create({
            'name': 'Percent tax',
            'type': 'percent',
            'amount': '0.1',
        })

        # product1 = cls.env.ref('product.product_product_28')
        # product2 = cls.env.ref('product.product_product_29')
        cls.order_lines = [
            (0, 0, {'product_id': cls.product1.id,
                    'name': 'Test',
                    'product_uom_qty': 10.0,
                    'price_unit': 100
                    }),
            (0, 0, {'product_id': cls.product2.id,
                    'name': 'Test2',
                    'product_uom_qty': 5.0,
                    'price_unit': 120
                    })]
        # set taxes on advance product
        cls.product_advance = cls.env.ref('sale.advance_product_0')
        # cls.tax = cls.env['account.tax'].create({'name': 'advance tax'})
        cls.product_advance.taxes_id = [(4, cls.account_tax.id)]

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

        # ----------------------------------------------
        #    Invoice a deposit of 500.0
        # ----------------------------------------------
        adv_wizard = self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method': 'fixed',
             'amount': 500.0,
             })
        adv_wizard.with_context(active_ids=[order.id]).create_invoices()
        self.assertTrue(order.invoice_ids)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 500.0)
        self.assertEqual(order.advance_amount_used, 0.0)

        # ---------------------------------------------------------------------
        #    Invoice the first sale order line and consume 200.0 from
        #    the deposit
        # ---------------------------------------------------------------------
        wizard = self.env['sale.order.line.make.invoice'].with_context(
            active_ids=[order.order_line[0].id]).create({})
        wizard.order_ids[0].advance_amount_to_use = 200.0
        res = wizard.with_context(open_invoices=True).make_invoices()
        invoice = self.env['account.invoice'].browse(res['res_id'])
        self.assertEqual(len(invoice.invoice_line), 2)
        inv_adv_line = self.env['account.invoice.line']
        for line in invoice.invoice_line:
            if line.product_id.id == self.product_advance.id:
                inv_adv_line = line
                break
        self.assertEqual(inv_adv_line.invoice_line_tax_id.id,
                         self.tax.id)
        self.assertEqual(invoice.amount_total, 800.0)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 300.0)
        self.assertEqual(order.advance_amount_used, 200.0)

        # ----------------------------------------------
        #    Invoice the remaining balance
        # ----------------------------------------------
        adv_wizar = self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method': 'all',
             })
        res = adv_wizar.with_context(active_ids=[order.id],
                                     open_invoices=True).create_invoices()
        invoice = self.env['account.invoice'].browse(res['res_id'])
        self.assertEqual(invoice.amount_total, 300.0)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 0.0)
        self.assertEqual(order.advance_amount_used, 500.0)

    def test_sale_order_partial_advance_all_lines(self):
        '''
            Test scenario
            - Create a sale order with 2 lines
            - Confirm the sale order
            - Invoice an advance
            - Invoice the 2 order lines at the same time, the whole advance
              amount should be used
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

        # ----------------------------------------------
        #    Invoice a deposit of 500.0
        # ----------------------------------------------
        adv_wizard = self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method': 'fixed',
             'amount': 500.0,
             })
        adv_wizard.with_context(active_ids=[order.id]).create_invoices()
        self.assertTrue(order.invoice_ids)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 500.0)
        self.assertEqual(order.advance_amount_used, 0.0)

        # ----------------------------------------------------------
        #    Invoice the 2 sale order line, the whole advance amount
        #    should be consumed
        # ----------------------------------------------
        wizard = self.env['sale.order.line.make.invoice'].with_context(
            active_ids=order.order_line.ids).create({})
        res = wizard.with_context(open_invoices=True).make_invoices()
        invoice = self.env['account.invoice'].browse(res['res_id'])
        self.assertEqual(invoice.amount_total, 1100.0)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 0.0)
        self.assertEqual(order.advance_amount_used, 500.0)

    def test_sale_order_partial_advance_refund(self):
        '''
            Test scenario
            - Create a sale order with 2 lines
            - Confirm the sale order
            - Invoice an advance
            - Make a refund for the advance
            - Invoice a new advance
            - Invoice the 2 order lines at the same time, the first advance
              amount should be ignored
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

        # ----------------------------------------------
        #    Invoice a deposit of 500.0
        # ----------------------------------------------
        adv_wizard = self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method': 'fixed',
             'amount': 500.0,
             })
        adv_wizard.with_context(active_ids=[order.id]).create_invoices()
        self.assertTrue(order.invoice_ids)
        self.assertEqual(order.advance_amount, 500.0)
        self.assertEqual(order.advance_amount_available, 500.0)
        self.assertEqual(order.advance_amount_used, 0.0)
        # ----------------------------------------------
        #    Refund the deposit of 500.0
        # ----------------------------------------------
        invoice = order.invoice_ids[0]
        invoice.signal_workflow('invoice_open')
        refund_wizard = self.env['account.invoice.refund'].with_context(
            active_ids=[invoice.id]).create({'filter_refund': 'cancel'})
        refund_wizard.invoice_refund()
        self.assertEqual(invoice.state, 'paid')

        # ----------------------------------------------
        #    Invoice a deposit of 300.0
        # ----------------------------------------------
        adv_wizard = self.env['sale.advance.payment.inv'].create(
            {'advance_payment_method': 'fixed',
             'amount': 300.0,
             })
        adv_wizard.with_context(active_ids=[order.id]).create_invoices()
        self.assertTrue(order.invoice_ids)
        self.assertEqual(order.advance_amount, 300.0)
        self.assertEqual(order.advance_amount_available, 300.0)
        self.assertEqual(order.advance_amount_used, 0.0)

        # ----------------------------------------------------------
        #    Invoice the 2 sale order line, the whole advance amount
        #    should be consumed
        # ----------------------------------------------
        wizard = self.env['sale.order.line.make.invoice'].with_context(
            active_ids=order.order_line.ids).create({})
        res = wizard.with_context(open_invoices=True).make_invoices()
        invoice = self.env['account.invoice'].browse(res['res_id'])
        self.assertEqual(invoice.amount_total, 1300.0)
        self.assertEqual(order.advance_amount, 300.0)
        self.assertEqual(order.advance_amount_available, 0.0)
        self.assertEqual(order.advance_amount_used, 300.0)
