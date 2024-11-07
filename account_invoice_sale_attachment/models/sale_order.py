# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    sale_document_attachment = fields.Binary(copy=False, attachment=True, readonly=True)

    def _prepare_sale_document_attachment_vals(self):
        pdf_data = self.env.ref("sale.action_report_saleorder")._render_qweb_pdf(
            self.ids
        )[0]
        return {
            "name": self.name,
            "type": "binary",
            "datas": base64.b64encode(pdf_data).decode("utf-8"),
            "res_model": self._name,
            "res_field": "sale_document_attachment",
            "res_id": self.id,
        }

    def _create_sale_document_attachment(self):
        self.ensure_one()
        self.env["ir.attachment"].create(
            [rec._prepare_sale_document_attachment_vals() for rec in self]
        )

    def _get_sale_document_attachments(self):
        for rec in self:
            if not rec.sale_document_attachment:
                rec._create_sale_document_attachment()
        return self.env["ir.attachment"].search(
            [
                ("res_id", "in", self.ids),
                ("res_model", "=", self._name),
                ("res_field", "=", "sale_document_attachment"),
            ]
        )
