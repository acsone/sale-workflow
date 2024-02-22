# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        """Apply general discount for sale order lines which are not created
        from sale order form view.
        """
        for vals in vals_list:
            if "discount" not in vals and "order_id" in vals:
                sale_order = self.env["sale.order"].browse(vals["order_id"])
                if sale_order.general_discount:
                    vals["discount"] = sale_order.general_discount
        return super().create(vals_list)

    @api.depends("order_id", "order_id.general_discount")
    def _compute_discount(self):
        res = super()._compute_discount()
        for line in self:
            if line.order_id.general_discount:
                line.discount = line.order_id.general_discount
        return res
