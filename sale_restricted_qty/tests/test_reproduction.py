from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestHistoricalDataBlocking(common.TransactionCase):
    def test_historical_data_blocking(self):
        # 1. Create product with no restrictions
        product = self.env["product.product"].create({"name": "Test Product"})

        # 2. Create and confirm SO with irregular quantity (not a multiple of 50)
        # 101 is not a multiple of 50
        so = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 101.0,
                        },
                    )
                ],
            }
        )
        so.action_confirm()

        # 3. Try to update product to enforce restriction
        # This SHOULD fail currently, and succeed after the fix
        # We catch the error to confirm reproduction
        product.write(
            {
                "sale_multiple_of_qty": 50.0,
                "sale_restrict_multiple_of_qty": "1",  # Blocking
                "is_sale_own_multiple_of_qty_set": True,
                "is_sale_own_restrict_multiple_of_qty_set": True,
            }
        )
        # If we reach here, success!
