# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestDiscountDisplay(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Product TEST", "type": "consu"}
        )
        cls.so = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.so_line = cls.env["sale.order.line"].create(
            {"order_id": cls.so.id, "product_id": cls.product.id, "price_unit": 30.75}
        )

    def test_sale_discount_value(self):
        self.so_line.discount = 10
        self.assertAlmostEqual(self.so_line.price_total_no_discount, 35.36)
        self.assertAlmostEqual(self.so_line.discount_total, 3.53)
        self.assertAlmostEqual(self.so.discount_total, 3.53)
        self.assertAlmostEqual(self.so.price_total_no_discount, 35.36)

    def test_sale_without_discount_value(self):
        self.assertEqual(self.so_line.price_total_no_discount, self.so_line.price_total)

    def test_unlink_after_compute_discount_total(self):
        # This test is to ensure that the unlink is still working with the
        # compute_discount_total method. It is a regression test for the
        # since the unlink raise an cache error when the compute_discount_total
        # assign values to the fields even if the values are the same when
        # the compute is called during the unlink process when models are
        # flushed before the unlink.
        self.so_line.discount = 10
        self.assertAlmostEqual(self.so_line.price_total_no_discount, 35.36)
        so_id = self.so.id
        self.so.unlink()
        # Check that the sale order is deleted
        self.assertFalse(self.env["sale.order"].browse(so_id).exists())
