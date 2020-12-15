# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    """Add the support for tiered pricing items.
       The main issue is that the unit price and description might change
       depending on the quantity. So when getting the price, we need to force the
       price field to be recomputed in the right context.
       Check what needs to be done on programmatic creation/update.
    """

    _inherit = "sale.order.line"

    is_tier_priced = fields.Boolean(
        default=False, compute="_compute_is_tier_priced", store=True
    )

    @api.depends("order_id.pricelist_id", "product_id")
    def _compute_is_tier_priced(self):
        for line in self:
            is_tier_priced = False
            if line.product_id:
                product = line._get_contextualized_product()
                pricelist = line.order_id.pricelist_id
                if pricelist:
                    is_tier_priced = pricelist.is_tier_priced_sale_line(product, line)
            line.is_tier_priced = is_tier_priced

    def get_sale_order_line_multiline_description_sale(self, product):
        """Enrich the description with the tier computation.
           TODO: improve the description, and update test accordingly.
        """
        res = super(SaleOrderLine, self).get_sale_order_line_multiline_description_sale(
            product
        )
        if self.is_tier_priced and self.product_uom_qty:
            context = {"lang": self.order_id.partner_id.lang}  # noqa  # used by _ below
            qps = product.tiered_qps
            computation = " + ".join("{:.2f} x {:.2f}".format(q, p) for q, p in qps)
            tier_description = _("Tiers: {}").format(computation)
            res = "\n".join([res, tier_description])
        return res

    def _get_contextualized_product(self):
        return self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
        )

    @api.onchange("price_unit")
    def onchange_price_unit(self):
        """For tier priced lines, we need to augment the description with the
           tier price computation -- everytime the price changes.
        """
        if self.is_tier_priced:
            product = self._get_contextualized_product()
            self.name = self.get_sale_order_line_multiline_description_sale(product)

    def _get_display_price(self, product):
        """Called by the onchange on product_id and product_uom_id.
           If the line is tier priced, the product price might change.
           Therefore we invalidate its cached value.
        """
        if self.is_tier_priced:
            product.invalidate_cache(fnames=["price"], ids=product.ids)
        return super(SaleOrderLine, self)._get_display_price(product)
