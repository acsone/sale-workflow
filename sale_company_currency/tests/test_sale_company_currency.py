from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # currencies
        cls.currency_usd = cls.env.ref("base.USD")
        cls.currency_eur = cls.env.ref("base.EUR")

        # Customer
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        # Company
        cls.company = cls.env.ref("base.main_company")

        # Products
        cls.product1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "type": "consu"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "consu"}
        )

        # Create a sale order with the same currency as the company
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
                "currency_id": cls.currency_usd.id,
            }
        )
        cls.sale_order_line_1 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order.id,
                "product_id": cls.product1.id,
                "product_uom_qty": 2,
                "price_unit": 50.0,
            }
        )
        cls.sale_order_line_2 = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order.id,
                "product_id": cls.product2.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
            }
        )

    def test_01_amount_total_curr_same_currency(self):
        """Test amount_total_curr when sale order currency matches company currency."""
        self.sale_order.currency_id = self.currency_usd
        self.sale_order._compute_amount_company()
        self.assertEqual(
            self.sale_order.amount_total_curr,
            self.sale_order.amount_total,
            "Amount in company currency should match the total amount when currencies "
            "are the same.",
        )
        self.assertEqual(
            self.sale_order.amount_untaxed_company_currency,
            self.sale_order.amount_untaxed,
        )
        self.assertEqual(
            self.sale_order_line_1.price_subtotal,
            self.sale_order_line_1.price_subtotal_company_currency,
        )
        self.assertEqual(
            self.sale_order_line_1.price_total,
            self.sale_order_line_1.price_total_company_currency,
        )

    def test_02_amount_total_curr_different_currency(self):
        """Test amount_total_curr when sale order currency differs from company
        currency."""
        self.sale_order.currency_id = self.currency_eur
        self.sale_order.currency_rate = 1.2
        self.sale_order._compute_amount_company()
        curr_rate = self.sale_order.currency_rate

        amount_total_curr_rounded = round(self.sale_order.amount_total_curr, 2)
        amount_total_converted_rounded = round(
            self.sale_order.amount_total * curr_rate, 2
        )
        self.assertEqual(
            amount_total_curr_rounded,
            amount_total_converted_rounded,
            msg=(
                "Amount in company currency should be converted "
                "using the currency rate."
            ),
        )
        self.assertEqual(
            self.sale_order.amount_untaxed_company_currency,
            round(self.sale_order.amount_untaxed * curr_rate, 2),
        )
        self.assertEqual(
            round(self.sale_order_line_1.price_subtotal * curr_rate, 2),
            self.sale_order_line_1.price_subtotal_company_currency,
        )
        self.assertEqual(
            round(self.sale_order_line_1.price_total * curr_rate, 2),
            self.sale_order_line_1.price_total_company_currency,
        )
