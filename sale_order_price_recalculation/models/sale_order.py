# -*- coding: utf-8 -*-
# Copyright 2014 Carlos Sánchez Cifuentes <csanchez@grupovermon.com>
# Copyright 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2015 Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def recalculate_prices(self):
        for line in self.mapped('order_line'):
            dict = line._convert_to_write(line.read()[0])
            if 'product_tmpl_id' in line._fields:
                dict['product_tmpl_id'] = line.product_tmpl_id
            line2 = self.env['sale.order.line'].new(dict)
            # we make this to isolate changed values:
            vals = self._get_update_price_fields_and_values(line2)
            line.write(vals)
        return True

    @api.model
    def _get_update_price_fields_and_values(self, in_memory_line):
        """Return a list of fields to update in the order lines.
        :return: dict of fields and values to update
        """
        in_memory_line.product_uom_change()
        in_memory_line._onchange_discount()
        return {
            'price_unit': in_memory_line.price_unit,
            'discount': in_memory_line.discount,
        }

    @api.multi
    def recalculate_names(self):
        for line in self.mapped('order_line').filtered('product_id'):
            # we make this to isolate changed values:
            line2 = self.env['sale.order.line'].new({
                'product_id': line.product_id,
            })
            line2.product_id_change()
            line.name = line2.name
        return True
