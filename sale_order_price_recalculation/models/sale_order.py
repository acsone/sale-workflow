# Copyright 2014 Carlos Sánchez Cifuentes <csanchez@grupovermon.com>
# Copyright 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2015 Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def recalculate_prices(self):
        # used by shopinvader
        return self.recompute_lines()

    def recalculate_names(self):
        # we keep it for compatibility
        return self.recompute_lines()

    def recompute_lines(self):
        to_process = self.mapped('order_line').filtered('product_id')
        to_process._compute_contract_cumulated_qty()
        to_process.recompute_price_and_description()
        return True
