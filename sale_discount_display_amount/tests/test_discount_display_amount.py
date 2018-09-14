# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestDiscountDisplay(TransactionCase):

    def setUp(self):
        super(TestDiscountDisplay, self).setUp()
        self.sale = self.env.ref("sale.sale_order_3")

    def test_sale_discount_value(self):
        first_line = self.sale.order_line[0]
        first_line.discount = 10
        second_line = self.sale.order_line[1]
        second_line.discount = 15

        self.assertAlmostEqual(first_line.price_total_no_discount, 307.5)
        self.assertAlmostEqual(first_line.discount_total, -30.75)
        self.assertAlmostEqual(second_line.price_total_no_discount, 70.0)
        self.assertAlmostEqual(second_line.discount_total, -10.5)
        self.assertAlmostEqual(self.sale.discount_total, -41.25)
        self.assertAlmostEqual(self.sale.price_total_no_discount, 377.5)
