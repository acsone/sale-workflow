# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo.api import Environment
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _add_column(cr, table, column, column_type="numeric"):
    query = """SELECT 1 FROM information_schema.columns
            WHERE table_name = %s
            AND column_name = %s"""
    cr.execute(query, (table, column))

    if not cr.fetchall():
        cr.execute("""
                ALTER TABLE %s ADD COLUMN %s %s;
            """, (table, column, column_type))


def pre_init_hook(cr):
    _logger.info("Create discount columns in database")
    _add_column(cr, 'sale_order', 'price_total_no_discount')
    _add_column(cr, 'sale_order', 'discount_total')
    _add_column(cr, 'sale_order_line', 'price_total_no_discount')
    _add_column(cr, 'sale_order_line', 'discount_total')


def post_init_hook(cr, registry):
    _logger.info("Compute discount columns")
    env = Environment(cr, SUPERUSER_ID, {})

    query = """
    update sale_order_line
    set price_total_no_discount = price_total
    where discount = 0.0
    """
    cr.execute(query)

    query = """
        update sale_order
        set price_total_no_discount = amount_total
        """
    cr.execute(query)

    query = """
    select distinct order_id from sale_order_line where discount > 0.0;
    """

    cr.execute(query)
    order_ids = cr.fetchall()

    orders = env['sale.order'].search([('id', 'in', order_ids)])
    orders.mapped('order_line')._compute_discount()
