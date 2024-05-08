# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_draft(self):
        res = super().action_draft()
        orders = self.filtered(lambda s: s.state == "draft")
        orders.order_line.write({"product_qty_canceled": 0})
        return res

    def _action_cancel(self):
        orders = self.filtered(lambda s: s.state != "cancel")
        orders_with_stock_move = orders.filtered(
            lambda o: any(
                line.qty_delivered_method == "stock_move" for line in o.order_line
            )
        )
        res = None
        if orders_with_stock_move:
            orders_with_stock_move = orders_with_stock_move.with_context(
                orders_cancel_by_running_procurements=orders_with_stock_move.ids
            )
            res = super(SaleOrder, orders_with_stock_move)._action_cancel()
        remaining_orders = orders - orders_with_stock_move
        if remaining_orders:
            res = super(SaleOrder, remaining_orders)._action_cancel()

        return res

    def _cancel_by_running_procurements(self):
        orders = self.filtered(lambda s: s.state != "cancel")
        orders.order_line.cancel_remaining_qty()
