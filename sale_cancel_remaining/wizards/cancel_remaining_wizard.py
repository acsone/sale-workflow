# Copyright 2018 Okia SPRL
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class CancelRemainingWizard(models.TransientModel):
    _name = "cancel.remaining.wizard"
    _description = "Cancel Remaining Wizard"

    def _get_sale_order_line(self):
        active_id = self._context.get("active_id")
        if not active_id:
            raise UserError(_("No sale order line ID found"))
        return self.env["sale.order.line"].browse(active_id)

    @api.model
    def _get_pickings_to_cancel(self, line):
        return line.order_id.picking_ids.filtered(
            lambda picking: picking.state not in ("cancel", "done")
        ) | line.order_id.picking_ids.filtered(
            lambda picking: picking.picking_type_code == "internal"
            and picking.state == "cancel"
            and picking.move_type == "one"
            and picking.backorder_id
        )

    @api.model
    def _check_pickings_to_cancel(self, line):
        pickings_to_cancel = self._get_pickings_to_cancel(line)
        if not pickings_to_cancel:
            raise UserError(_("No picking can be canceled"))

    @api.model
    def _get_moves_to_cancel(self, line):
        moves_to_cancel = line.mapped("move_ids").filtered(
            lambda m: m.state not in ("done", "cancel")
        )
        return (
            self.env["stock.move"].search(
                [("first_move_id", "in", moves_to_cancel.ids)]
            )
            | moves_to_cancel
        )

    def cancel_remaining_qty(self):
        line = self._get_sale_order_line()
        if not line.can_cancel_remaining_qty:
            return False
        self._check_pickings_to_cancel(line)
        cancel_moves = self._get_moves_to_cancel(line)
        cancel_moves._action_cancel()
        line.write({"product_qty_canceled": line.product_qty_remains_to_deliver})
        return True
