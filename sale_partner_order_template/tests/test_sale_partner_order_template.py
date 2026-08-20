# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestSalePartnerOrderTemplate(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id |= cls.env.ref(
            "sale_management.group_sale_order_template"
        )
        cls.order_template = cls.env["sale.order.template"].create(
            {"name": "Test Quotation Template"}
        )
        cls.partner.sale_order_template_id = cls.order_template
        cls.partner_without_template = cls.env["res.partner"].create(
            {"name": "Partner w/o template"}
        )

    def test_order_template_from_partner(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        order = order_form.save()
        self.assertEqual(order.sale_order_template_id, self.order_template)

    def test_no_order_template_on_partner(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner_without_template
        order = order_form.save()
        self.assertFalse(order.sale_order_template_id)

    def test_order_template_reset_on_partner_change(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        order_form.partner_id = self.partner_without_template
        order = order_form.save()
        self.assertFalse(order.sale_order_template_id)
