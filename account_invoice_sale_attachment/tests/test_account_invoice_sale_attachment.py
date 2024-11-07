# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import Form, TransactionCase


class TestAccountInvoiceSaleAttachment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, discard_logo_check=True))
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env.ref("product.product_product_1")
        cls.product.invoice_policy = "order"
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "state": "sale",
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()
        cls.invoice = cls.sale_order._create_invoices()

    def _get_sale_document_attachment(self, sale_order):
        return self.env["ir.attachment"].search(
            [
                ("res_id", "=", sale_order.id),
                ("res_model", "=", sale_order._name),
                ("res_field", "=", "sale_document_attachment"),
            ]
        )

    def _create_invoice_send_wizard_form(self):
        action = self.invoice.action_invoice_sent()
        return Form(
            self.env[action.get("res_model")].with_context(**action.get("context"))
        )

    def test_0(self):
        """if the option is not disabled at the partner level, nothing happens"""
        self.partner.allow_invoice_sale_order_attachment = False
        action = self.invoice.action_invoice_sent()
        self.assertFalse(self._get_sale_document_attachment(self.sale_order))
        wizard_form = Form(
            self.env[action.get("res_model")].with_context(**action.get("context"))
        )
        self.assertEqual(len(wizard_form.attachment_ids), 1)

    def test_1(self):
        """if the option is not enabled at the partner level, the document of the
        linked sale order will be added to the email send wizard"""
        self.partner.allow_invoice_sale_order_attachment = True
        wizard_form = self._create_invoice_send_wizard_form()
        self.assertTrue(self._get_sale_document_attachment(self.sale_order))
        self.assertEqual(len(wizard_form.attachment_ids), 2)
        wizard = wizard_form.save()
        self.assertIn(
            self._get_sale_document_attachment(self.sale_order), wizard.attachment_ids
        )

    def test_2(self):
        """check it works even for multiple orders linked to one invoice"""
        self.partner.allow_invoice_sale_order_attachment = True
        sale_order_2 = self.sale_order.copy()
        sale_order_2.action_confirm()
        self.invoice.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 2,
                            "price_unit": 100,
                            "sale_line_ids": [Command.link(sale_order_2.order_line.id)],
                        }
                    )
                ]
            }
        )
        self.assertEqual(
            len(self.invoice.invoice_line_ids.sale_line_ids.mapped("order_id")), 2
        )
        wizard_form = self._create_invoice_send_wizard_form()
        self.assertEqual(len(wizard_form.attachment_ids), 3)
        wizard = wizard_form.save()
        self.assertIn(
            self._get_sale_document_attachment(self.sale_order), wizard.attachment_ids
        )
        self.assertIn(
            self._get_sale_document_attachment(sale_order_2), wizard.attachment_ids
        )
