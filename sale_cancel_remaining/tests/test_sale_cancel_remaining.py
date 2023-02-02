# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import TestSaleCancelRemainingBase


class TestSaleCancelRemaining(TestSaleCancelRemainingBase):
    def test_cancel_remaining_qty_not_started_picking(self):
        line = self.sale.order_line
        self.assertEqual(line.product_qty_remains_to_deliver, 10)
        self.assertEqual(line.product_qty_canceled, 0)
        self.wiz.with_context(active_id=line.id).cancel_remaining_qty()
        self.assertEqual(line.product_qty_remains_to_deliver, 0)
        self.assertEqual(line.product_qty_canceled, 10)

    def test_cancel_remaining_qty_for_backorder_all_at_once(self):
        """check backorder canceled"""
        sale2 = self._add_done_sale_order(picking_policy="one")
        line = sale2.order_line
        pick = sale2.picking_ids.filtered(
            lambda picking: picking.picking_type_code == "internal"
            and picking.state not in ("cancel", "done")
        )
        backorder = pick._create_backorder()
        backorder.with_context(force_cancel=True).action_cancel()
        self.wiz.with_context(active_id=sale2.order_line.id).cancel_remaining_qty()
        self.assertEqual(line.product_qty_remains_to_deliver, 0)
        self.assertEqual(line.product_qty_canceled, 10)

    def test_cancel_remaining_qty(self):
        """check all picks of the delivery chain are canceled"""
        picks = self.sale.picking_ids
        self.assertEqual(len(picks), 2)
        self.assertEqual(self.sale.order_line.product_qty_remains_to_deliver, 10)
        self.wiz.with_context(active_id=self.sale.order_line.id).cancel_remaining_qty()
        self.assertSetEqual(set(picks.mapped("state")), {"cancel"})
        self.assertEqual(self.sale.order_line.product_qty_canceled, 10)
        self.assertEqual(self.sale.order_line.product_qty_remains_to_deliver, 0)

    def test_cancel_canceled_order(self):
        self.sale.picking_ids.action_cancel()
        with self.assertRaises(UserError):
            self.wiz.with_context(
                active_id=self.sale.order_line.id
            ).cancel_remaining_qty()
