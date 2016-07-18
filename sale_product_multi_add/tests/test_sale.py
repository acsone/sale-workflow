# -*- coding: utf-8 -*-
# © 2016  Cédric Pigeon, Acsone SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import openerp.tests.common as common


class TestSale(common.TransactionCase):

    def setUp(self):
        common.TransactionCase.setUp(self)

        self.product_35 = self.env.ref("product.product_product_35")
        self.product_36 = self.env.ref("product.product_product_36")

    def test_import_product(self):
        """ Create SO
            Import products
            Check products are presents
        """

        so = self.env["sale.order"].create(
            {"partner_id": self.env.ref("base.res_partner_2").id,
             })

        wiz_obj = self.env['sale.import.products']
        wizard = wiz_obj.with_context(active_id=so.id,
                                      active_model='sale.order')

        products = [(6, 0, [self.product_35.id, self.product_36.id])]

        wizard_id = wizard.create({'products': products,
                                   'quantity': 5.0})

        wizard_id.select_products()

        self.assertEqual(len(so.order_line), 2)

        for line in so.order_line:
            self.assertEqual(line.product_uos_qty, 5.0)
