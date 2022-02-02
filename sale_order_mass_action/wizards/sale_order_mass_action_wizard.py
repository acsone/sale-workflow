# Copyright (C) 2015-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderMassActionWizard(models.TransientModel):

    _name = "sale.order.mass.action.wizard"

    confirm = fields.Boolean(
        help="Check this box if you want to confirm all the selected quotations."
    )

    def _get_sale_order_confirm_domain(self):
        return [
            ("id", "in", self.env.context.get("active_ids")),
            ("state", "in", ("draft", "sent")),
        ]

    def apply_button(self):
        sale_order_obj = self.env["sale.order"]
        if self.env.context.get("active_model") != "sale.order":
            return
        for wizard in self.filtered("confirm"):
            sale_orders = sale_order_obj.search(wizard._get_sale_order_confirm_domain())
            sale_orders.action_confirm()
        return True
