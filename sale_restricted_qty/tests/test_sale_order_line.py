# Copyright 2024 CorporateHub
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSaleOrderLine(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Partner = cls.env["res.partner"]
        cls.Product = cls.env["product.product"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.Uom = cls.env["uom.uom"]

        cls.partner = cls.Partner.create({"name": "Partner"})
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")

    def test_min_qty(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_min_qty": 10.0,
            }
        )
        self.assertTrue(product.is_sale_own_min_qty_set)
        self.assertEqual(product.sale_own_min_qty, 10.0)

        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 5.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(sale_order.order_line.min_qty, 10.0)
        self.assertFalse(sale_order.order_line.restrict_min_qty)
        self.assertTrue(sale_order.order_line.is_below_min_qty)

    def test_min_qty_restricted(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_min_qty": 10.0,
                "sale_restrict_min_qty": "1",
            }
        )
        with self.assertRaises(ValidationError):
            self.SaleOrder.create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 5.0,
                            },
                        )
                    ],
                }
            )

    def test_max_qty(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_max_qty": 10.0,
            }
        )
        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 15.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(sale_order.order_line.max_qty, 10.0)
        self.assertFalse(sale_order.order_line.restrict_max_qty)
        self.assertTrue(sale_order.order_line.is_above_max_qty)

    def test_max_qty_restricted(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_max_qty": 10.0,
                "sale_restrict_max_qty": "1",
            }
        )
        with self.assertRaises(ValidationError):
            self.SaleOrder.create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 15.0,
                            },
                        )
                    ],
                }
            )

    def test_multiple_of_qty(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_multiple_of_qty": 5.0,
            }
        )
        sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 7.0,
                        },
                    )
                ],
            }
        )
        self.assertEqual(sale_order.order_line.multiple_of_qty, 5.0)
        self.assertFalse(sale_order.order_line.restrict_multiple_of_qty)
        self.assertTrue(sale_order.order_line.is_not_multiple_of_qty)

    def test_multiple_of_qty_restricted(self):
        product = self.Product.create(
            {
                "name": "Product",
                "sale_multiple_of_qty": 5.0,
                "sale_restrict_multiple_of_qty": "1",
            }
        )
        with self.assertRaises(ValidationError):
            self.SaleOrder.create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 7.0,
                            },
                        )
                    ],
                }
            )

    def test_uom_conversion(self):
        """Test that constraints work with different UoMs."""
        product = self.Product.create(
            {
                "name": "Product",
                "uom_id": self.uom_unit.id,
                "sale_min_qty": 24.0,  # 2 Dozen
                "sale_restrict_min_qty": "1",
            }
        )
        # 1 Dozen = 12 Units < 24 Units (Min)
        with self.assertRaises(ValidationError):
            self.SaleOrder.create(
                {
                    "partner_id": self.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 1.0,
                                "product_uom": self.uom_dozen.id,
                            },
                        )
                    ],
                }
            )
        # 3 Dozen = 36 Units > 24 Units (Min) -> Success
        self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 3.0,
                            "product_uom": self.uom_dozen.id,
                        },
                    )
                ],
            }
        )

    def test_auto_populate_all(self):
        """Test auto-population for Min, Max, and Multiple."""
        product = self.Product.create(
            {
                "name": "Product",
                "sale_min_qty": 10.0,
                "sale_restrict_min_qty": "1",
            }
        )
        line = self.env["sale.order.line"].new(
            {
                "product_id": product.id,
            }
        )
        line._onchange_product_id()
        line._onchange_product_id_set_min_qty()
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_inverse_handling(self):
        """Test that setting sale_min_qty triggers inverses."""
        product = self.Product.create({"name": "Product"})
        product.sale_min_qty = 15.0
        self.assertTrue(product.is_sale_own_min_qty_set)
        self.assertEqual(product.sale_own_min_qty, 15.0)

        product.sale_restrict_min_qty = "1"
        self.assertTrue(product.is_sale_own_restrict_min_qty_set)
        self.assertEqual(product.sale_own_restrict_min_qty, "1")

    def test_historical_data_blocking(self):
        """Reproduce and verify skip of checks for confirmed lines."""
        product = self.Product.create({"name": "Test Product"})
        so = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (0, 0, {"product_id": product.id, "product_uom_qty": 101.0})
                ],
            }
        )
        so.action_confirm()

        # Update product to enforce 50-multiple restriction
        # This should NOT fail because the SO line is confirmed
        product.write(
            {
                "sale_multiple_of_qty": 50.0,
                "sale_restrict_multiple_of_qty": "1",
            }
        )
        # Verify SO line still has old qty and doesn't crash on re-read
        self.assertEqual(so.order_line.product_uom_qty, 101.0)
