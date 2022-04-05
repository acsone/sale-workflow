# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("create column for shipping cost on sale orders")
    cr.execute(
        """
ALTER TABLE sale_order ADD COLUMN item_amount_total DOUBLE PRECISION;
ALTER TABLE sale_order ADD COLUMN shipping_amount_total DOUBLE PRECISION;
ALTER TABLE sale_order ADD COLUMN item_amount_untaxed DOUBLE PRECISION;
ALTER TABLE sale_order ADD COLUMN shipping_amount_tax DOUBLE PRECISION;
ALTER TABLE sale_order ADD COLUMN item_amount_tax DOUBLE PRECISION;
ALTER TABLE sale_order ADD COLUMN shipping_amount_untaxed DOUBLE PRECISION;

WITH shipping_cost AS (
    SELECT
        order_id,
        sum(price_subtotal) as shipping_amount_untaxed,
        sum(price_total) as shipping_amount_total,
        sum(price_tax) as shipping_amount_tax
    FROM
        sale_order_line
    WHERE
        is_delivery
    GROUP BY order_id
)
UPDATE
    sale_order
SET
    shipping_amount_untaxed=sc.shipping_amount_untaxed,
    shipping_amount_total=sc.shipping_amount_total,
    shipping_amount_tax= sc.shipping_amount_tax,
    item_amount_total=amount_total - sc.shipping_amount_total,
    item_amount_untaxed=amount_untaxed - sc.shipping_amount_untaxed,
    item_amount_tax=amount_tax - sc.shipping_amount_tax
FROM (
    SELECT
        *
    FROM
    shipping_cost
) AS sc
WHERE
    sc.order_id=id
;
        """
    )
