# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cancelled_by_refund = fields.Boolean('Cancelled by refund',
                                         compute='_is_cancelled_by_refund')

    @api.one
    @api.depends('payment_ids')
    def _is_cancelled_by_refund(self):
        cancelled = False
        for move in self.payment_ids:
            if move.invoice and move.invoice.type == 'out_refund' and \
                    move.invoice.origin == self.internal_number:
                cancelled = True
                break
        self.cancelled_by_refund = cancelled
