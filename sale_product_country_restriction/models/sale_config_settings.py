# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleConfigSettings(models.TransientModel):

    _inherit = 'sale.config.settings'

    default_country_restriction_id = fields.Many2one(
        comodel_name='product.country.restriction',
        string='Default Customer Country Restriction',
        related='company_id.default_country_restriction_id',
        help="This is the default Country Restriction set on partner when"
             "creating it."
    )
