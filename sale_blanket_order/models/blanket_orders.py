# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo.tools import float_is_zero


class BlanketOrder(models.Model):
    _name = 'sale.blanket.order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Blanket Order'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.model
    def _default_company(self):
        return self.env.user.company_id

    name = fields.Char(
        default='Draft',
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', readonly=True,
        states={'draft': [('readonly', False)]})
    lines_ids = fields.One2many(
        'sale.blanket.order.line', 'order_id', string='Order lines')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one(
        'res.currency', related='pricelist_id.currency_id', readonly=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', readonly=True,
        states={'draft': [('readonly', False)]})
    confirmed = fields.Boolean()
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('opened', 'Opened'),
        ('expired', 'Expired'),
    ], compute='_compute_state', store=True)
    validity_date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]})
    client_order_ref = fields.Char(
        string='Customer Reference', copy=False, readonly=True,
        states={'draft': [('readonly', False)]})
    note = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one(
        'res.users', string='Salesperson', readonly=True,
        states={'draft': [('readonly', False)]})
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', change_default=True,
        default=_get_default_team, readonly=True,
        states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(
        'res.company', string='Company', default=_default_company,
        readonly=True,
        states={'draft': [('readonly', False)]})
    sale_count = fields.Integer(compute='_compute_sale_count')

    @api.multi
    def _get_sale_orders(self):
        lines = self.mapped('lines_ids')
        sale_lines = lines.mapped('sale_order_lines_ids')
        sale_orders = sale_lines.mapped('order_id')
        sale_orders_ids = list(set(sale_orders.ids))
        return self.env['sale.order'].browse(sale_orders_ids)

    @api.multi
    @api.depends('lines_ids.remaining_qty')
    def _compute_sale_count(self):
        for blanket_order in self:
            blanket_order.sale_count = len(blanket_order._get_sale_orders())

    @api.multi
    @api.depends(
        'lines_ids.remaining_qty',
        'validity_date',
        'confirmed'
    )
    def _compute_state(self):
        today = fields.Date.today()
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for order in self:
            if not order.confirmed:
                order.state = 'draft'
            elif order.validity_date <= today:
                order.state = 'expired'
            elif float_is_zero(sum(order.lines_ids.mapped('remaining_qty')),
                               precision_digits=precision):
                order.state = 'expired'
            else:
                order.state = 'opened'

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        """
        if not self.partner_id:
            self.payment_term_id = False
            return

        values = {
            'pricelist_id': (self.partner_id.property_product_pricelist and
                             self.partner_id.property_product_pricelist.id or
                             False),
            'payment_term_id': (self.partner_id.property_payment_term_id and
                                self.partner_id.property_payment_term_id.id or
                                False),
        }

        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    @api.multi
    def _validate(self):
        try:
            today = fields.Date.today()
            for order in self:
                assert order.validity_date, _("Validity date is mandatory")
                assert order.validity_date > today, \
                    _("Validity date must be in the future")
                assert order.partner_id, _("Partner is mandatory")
                assert len(order.lines_ids) > 0, _("Must have some lines")
                order.lines_ids._validate()
        except AssertionError as e:
            raise Warning(e.message)

    @api.multi
    def action_confirm(self):
        self._validate()
        for order in self:
            sequence_obj = self.env['ir.sequence']
            if order.company_id:
                sequence_obj = sequence_obj.with_context(
                    force_company=order.company_id.id)
            name = sequence_obj.next_by_code('sale.blanket.order')
            order.write({'confirmed': True, 'name': name})
        return True

    @api.multi
    def action_view_sale_orders(self):
        sale_orders = self._get_sale_orders()
        action = self.env.ref('sale.action_orders').read()[0]
        if len(sale_orders) > 0:
            action['domain'] = [('id', 'in', sale_orders.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def expire_orders(self):
        today = fields.Date.today()
        expired_orders = self.search([
            ('state', '=', 'opened'),
            ('validity_date', '<=', today),
        ])
        expired_orders.modified(['validity_date'])
        expired_orders.recompute()


class BlanketOrderLine(models.Model):
    _name = 'sale.blanket.order.line'
    _description = 'Blanket Order Line'

    sequence = fields.Integer()
    order_id = fields.Many2one('sale.blanket.order', required=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    product_uom = fields.Many2one(
        'product.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Price', required=True)
    original_qty = fields.Float(string='Original quantity', required=True)
    ordered_qty = fields.Float(
        string='Ordered quantity', compute='_compute_quantities', store=True)
    invoiced_qty = fields.Float(
        string='Invoiced quantity', compute='_compute_quantities', store=True)
    remaining_qty = fields.Float(
        string='Remaining quantity', compute='_compute_quantities', store=True)
    delivered_qty = fields.Float(
        string='Delivered quantity', compute='_compute_quantities', store=True)
    sale_order_lines_ids = fields.One2many(
        'sale.order.line', 'blanket_line_id', string='Sale order lines')
    company_id = fields.Many2one(
        'res.company', related='order_id.company_id', store=True)

    @api.multi
    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    @api.multi
    @api.depends(
        'sale_order_lines_ids.blanket_line_id',
        'sale_order_lines_ids.product_uom_qty',
        'sale_order_lines_ids.qty_delivered',
        'sale_order_lines_ids.qty_invoiced',
        'original_qty'
    )
    def _compute_quantities(self):
        for line in self:
            sale_lines = line.sale_order_lines_ids
            line.ordered_qty = sum(l.product_uom_qty for l in sale_lines)
            line.invoiced_qty = sum(l.qty_invoiced for l in sale_lines)
            line.delivered_qty = sum(l.qty_delivered for l in sale_lines)
            line.remaining_qty = line.original_qty - line.ordered_qty

    @api.multi
    def _validate(self):
        try:
            for line in self:
                assert line.price_unit > 0.0, \
                    _("Price must be greater than zero")
                assert line.original_qty > 0.0, \
                    _("Quantity must be greater than zero")
        except AssertionError as e:
            raise Warning(e.message)
