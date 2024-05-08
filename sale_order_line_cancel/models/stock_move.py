# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        sale_moves = self.filtered(
            lambda m: m.sale_line_id and m.state not in ("done", "cancel")
        )
        res = super()._action_cancel()
        sale_lines = sale_moves.filtered(lambda m: m.state == "cancel").sale_line_id
        for line in sale_lines:
            # Update SO line qty canceled only when all remaining moves are canceled
            if line._get_moves_to_cancel():
                continue
            line.product_qty_canceled = line.qty_to_deliver
        return res
