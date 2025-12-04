from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import calendar
from datetime import  date


class SalesTeamTarget(models.Model):
    _name = 'sales.team.target'
    _rec_name = 'name'
    _description = 'Sales Team Target'

    name = fields.Char(string="Target Sequence", default=_('New'), copy=False)
    state = fields.Selection(string="Sales Target Status",
                             selection=[('draft', 'Draft'),
                                        ('running', 'Running'),
                                        ('closed', 'Closed'),
                                        ('canceled', 'Canceled'),
                                        ],
                             default='draft')
    team_id = fields.Many2one(comodel_name="crm.team", string="Sales Team", readonly={'state', '!=', 'draft'})
    member_ids = fields.Many2many(related='team_id.member_ids')
    sales_person_id = fields.Many2one(comodel_name="res.users", string="Sales Person",
                                      domain="[('id','in',member_ids)]",
                                      readonly={'state', '!=', 'draft'}, copy=False)
    policy_id = fields.Many2one(comodel_name="commission.policy", string="Commission Policy",
                                readonly={'state', '!=', 'draft'})
    target_amount = fields.Float(readonly={'state', '!=', 'draft'})
    achievement_amount = fields.Float(string="Achievement (Amount)",
                                      compute='compute_achievement_amount',
                                      store=True)
    achievement_percent = fields.Float(string="Achievement (%)",
                                       compute='compute_achievement_percentage',
                                       store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id, required=True,
                                  readonly={'state', '!=', 'draft'})
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True, readonly={'state', '!=', 'draft'})
    target_achievement = fields.Selection(selection=[('confirmed_sale', 'Confirmed Sales Order'),
                                                     ('invoice', 'Invoice'),
                                                     ('paid_invoice', 'Paid Invoice')],
                                          required=True,
                                          readonly={'state', '!=', 'draft'})
    check_close_date = fields.Boolean(compute='_compute_check_close_date')
    target_calc_based_on = fields.Selection(string="Target Calculation Based on",
                                            selection=[('all_product', 'All Product'),
                                                       ('product', 'Product'),
                                                       ('product_category', 'Product Category')], required=True,
                                            readonly={'state', '!=', 'draft'},
                                            default='all_product')
    product_categ_ids = fields.Many2many('product.category', relation="sales_target_product_category_rel",
                                         string="Product Categories",
                                         readonly={'state', '!=', 'draft'})
    target_commission_line_ids = fields.One2many('sales.team.target.commissions', 'target_commission_id',
                                                 string="Sales Team Target Commission")
    commission_percentage = fields.Float(string="Commission Percentage", compute="compute_commission_percentage")
    amount = fields.Float(string="Amount", compute='compute_commission_amount')
    product_ids = fields.Many2many('product.product', relation="sales_target_product_rel", string="Services",
                                   readonly={'state', '!=', 'draft'})

    @api.onchange('policy_id')
    def _onchange_policy_id(self):
        for rec in self:
            if rec.policy_id and rec.policy_id.target_type == 'amount':
                last_policy_line = self.env['policy.details'].search([('policy_id', '=', rec.policy_id.id)],
                                                                     order="id desc", limit=1)
                rec.target_amount = last_policy_line.target_to

    @api.model
    def generate_sales_target_commission(self, running_date=False):
        if running_date:
            if not isinstance(running_date, date):
                running_date = fields.Date.from_string(running_date)
        else:
            running_date = fields.Date.today()
        targets = self.env['sales.team.target'].search([('date_to', '=', running_date)])
        for target in targets:
            commission_line = self.env['sales.commission.lines'].search([('target_id', '=', target.id)], limit=1)
            if not commission_line:
                commission_line = self.env['sales.commission.lines'].create({
                    'sales_commission_reference': self.env['ir.sequence'].next_by_code('sales.commission.lines'),
                    'commission_date': target.date_to,
                    'sales_team_id': target.team_id.id,
                    'user_id': target.sales_person_id.id,
                    'commission_percentage': target.commission_percentage,
                    'amount': target.amount,
                    'target_id': target.id,
                    'currency_id': self.env.company.currency_id.id
                })
            for line in target.target_commission_line_ids:
                line.sales_commission_line_id = commission_line.id
            commission_line.write({
                'commission_percentage': target.commission_percentage,
                'amount': target.amount
            })
            target.close()

    @api.depends('achievement_percent', 'policy_id', 'policy_id.target_type', 'achievement_amount')
    def compute_commission_percentage(self):
        for rec in self:
            percent = 0.0
            if rec.policy_id:
                commission_policy = self.env['commission.policy'].search([('state', '=', 'active'),
                                                                          ('id', '=', rec.policy_id.id)], limit=1)
                commission_policy_lines = commission_policy.mapped('details_ids')
                for line in commission_policy_lines:
                    if commission_policy.target_type == 'percentage' and rec.achievement_percent:
                        if line.target_from < rec.achievement_percent <= line.target_to:
                            percent = line.commission
                        elif rec.achievement_percent > commission_policy_lines[-1].target_to:
                            percent = commission_policy_lines[-1].commission
                    elif commission_policy.target_type == 'amount' and rec.achievement_amount:
                        if line.target_from < rec.achievement_amount <= line.target_to:
                            percent = line.commission
                        elif rec.achievement_amount > commission_policy_lines[-1].target_to:
                            percent = commission_policy_lines[-1].commission
                rec.commission_percentage = percent
            else:
                rec.commission_percentage = 0.0

    @api.depends('commission_percentage', 'achievement_amount')
    def compute_commission_amount(self):
        for rec in self:
            if rec.commission_percentage and rec.achievement_amount:
                rec.amount = (rec.commission_percentage / 100) * rec.achievement_amount
            else:
                rec.amount = 0.0

    def get_related_record_line(self, target_type):
        related_record_line = ''
        if target_type == 'confirmed_sale':
            related_record_line = 'order_line'
        elif target_type in ['invoice', 'paid_invoice']:
            related_record_line = 'invoice_line_ids'
        return related_record_line

    def create_commission_general_target(self, lines, related_record, target_type, sales_user_target):
        vals = []
        commission_target_general_obj = self.env['sales.team.target.commissions']
        for line in lines:
            if target_type == 'confirmed_sale':
                vals.append({
                    'name': line.order_id.name,
                    'product_id': line.product_id.id,
                    'product_desc': line.name,
                    'uom_id': line.product_uom.id,
                    'quantity': line.product_uom_qty,
                    'price_subtotal': line.price_subtotal,
                    'price': line.price_unit,
                    'target_achievement': target_type,
                    'sale_order_line_id': line.id,
                    'target_commission_id': sales_user_target.id,
                    'sale_id': line.order_id.id,
                    'is_commission': True
                })
            elif target_type == 'delivered_sales':
                commissioned_products = self.env['sales.team.target.commissions'].search(
                    [('is_commission', '=', True),
                     ('sale_id', '=', line.order_id.id)])
                if not commissioned_products:
                    vals.append({
                        'name': related_record.name,
                        'product_id': line.product_id.id,
                        'product_desc': line.name,
                        'uom_id': line.product_uom.id,
                        'quantity': line.product_uom_qty,
                        'price_subtotal': line.price_subtotal,
                        'price': line.price_unit,
                        'target_achievement': target_type,
                        'target_commission_id': sales_user_target.id,
                        'sale_id': line.order_id.id,
                        'is_commission': True
                    })
            elif target_type in ['invoice', 'paid_invoice']:
                invoice_origin = self.env['sale.order'].search([('name', '=', line.move_id.invoice_origin)], limit=1)
                commissioned_products = self.env['sales.team.target.commissions'].search(
                    [('is_commission', '=', True),
                     ('sale_id', '=', invoice_origin.id)])
                if not commissioned_products:
                    vals.append({
                        'name': line.move_id.name,
                        'product_id': line.product_id.id,
                        'product_desc': line.name,
                        'uom_id': line.product_uom_id.id,
                        'quantity': line.quantity,
                        'price_subtotal': line.price_subtotal,
                        'price': line.price_unit,
                        # 'target_achievement': target_type,
                        'account_move_line_id': line.id,
                        'target_commission_id': sales_user_target.id,
                        'sale_id': invoice_origin.id,
                        'is_commission': True

                    })
        commission_target_general_obj.create(vals)

    def is_valid_target(self, target_type, date, user, related_record):
        sales_user_target = self.search(
            [('sales_person_id', '=', user.id),
             ('state', '=', 'running'),
             ('date_from', '<=', date),
             ('date_to', '>=', date),
             ('target_achievement', '=', target_type)])
        for target in sales_user_target:
            if target_type == 'delivered_sales':
                related_line_field = related_record.sale_id.order_line
                lines = related_record.sale_id.order_line
            else:
                related_line_field = self.get_related_record_line(target_type)
                lines = related_record[related_line_field]
            if target:
                if target.target_calc_based_on == 'product_category':
                    filtered_lines = lines.filtered(
                        lambda product: product.product_id.categ_id.id in target.product_categ_ids.ids)
                elif target.target_calc_based_on == 'product':
                    filtered_lines = lines.filtered(
                        lambda product: product.product_id.id in target.product_ids.ids)
                else:
                    filtered_lines = lines
                self.create_commission_general_target(filtered_lines, related_record, target_type, target)

    def is_not_valid_target(self, target_type, lines):
        commission_target_general_obj = False
        if target_type == 'confirmed_sale':
            commission_target_general_obj = self.env['sales.team.target.commissions'].search(
                [('sale_order_line_id', 'in', lines.ids)])
        elif target_type in ['invoice', 'paid_invoice']:
            commission_target_general_obj = self.env['sales.team.target.commissions'].search(
                [('account_move_line_id', 'in', lines.ids)])
        commission_target_general_obj.unlink()

    @api.depends('target_amount', 'target_commission_line_ids')
    def compute_achievement_amount(self):
        for rec in self:
            rec.achievement_amount = sum(rec.target_commission_line_ids.mapped('price_subtotal'))

    @api.depends('target_amount', 'target_commission_line_ids', 'achievement_amount')
    def compute_achievement_percentage(self):
        for rec in self:
            if rec.target_amount > 0.0:
                rec.achievement_percent = (rec.achievement_amount / rec.target_amount) * 100
            else:
                rec.achievement_percent = 0.0

    @api.onchange('date_from')
    def _onchange_date_from(self):
        for rec in self:
            if rec.date_from:
                rec.date_from = rec.date_from.replace(day=1)

    # @api.onchange('date_to')
    # def _onchange_date_to(self):
    #     for rec in self:
    #         if rec.date_to:
    #             month_days = calendar.monthrange(rec.date_to.year, rec.date_to.month)[1]
    #             rec.date_to = rec.date_to.replace(day=month_days)
    @api.onchange('target_calc_based_on')
    def onchange_target_calc_based_on(self):
        self.ensure_one()
        if self.target_calc_based_on and self.target_calc_based_on == 'all_product':
            self.product_categ_ids = False
        elif self.target_calc_based_on and self.target_calc_based_on == 'product':
            self.product_categ_ids = False

    @api.onchange('date_to')
    def _onchange_date_to(self):
        for rec in self:
            if rec.date_to:
                month_days = calendar.monthrange(rec.date_to.year, rec.date_to.month)[1]
                rec.date_to = rec.date_to.replace(day=month_days)

    @api.constrains('date_from', 'date_to', 'sales_person_id', 'target_calc_based_on', 'product_categ_ids',
                    'product_ids')
    def _constrain_date_from_to_sales_person(self):
        for rec in self:
            domain = [('id', '!=', rec.id),
                      ('sales_person_id', '=', rec.sales_person_id.id),
                      ('state', '!=', 'canceled'),
                      ('date_to', '>=', rec.date_from),
                      ('date_from', '<=', rec.date_to)]
            previous_periods = self.search(domain)
            if previous_periods:
                for period in previous_periods:
                    if period.target_calc_based_on in ['all_product', 'product_category',
                                                       'product'] and rec.target_calc_based_on == 'all_product':
                        raise ValidationError(
                            _(
                                "Sorry, the selected sales person has a target at the same period ({})").format(
                                period.name))
                    elif rec.product_categ_ids:
                        for categ in rec.product_categ_ids:
                            if categ.id in period.product_categ_ids.ids:
                                raise ValidationError(_(
                                    "Sorry, the selected sales person has a target at the same period ({}) and ({}) Category is duplicated").format(
                                    period.name, categ.display_name))
                        product_categ_ids = self.env['product.product'].search(
                            [('categ_id', 'in', rec.product_categ_ids.ids)])
                        for product in product_categ_ids:
                            if product.id in period.product_ids.ids:
                                raise ValidationError(_(
                                    "Sorry, the selected sales person has a target at the same period ({}) and ({}) Product in period category products").format(
                                    period.name, product.display_name))
                    elif rec.product_ids:
                        for product in rec.product_ids:
                            if product.categ_id.id in period.product_categ_ids.ids:
                                raise ValidationError(_(
                                    "Sorry, the selected sales person has a target at the same period"
                                    " ({}) and ({}) Product in period category products").format(
                                    period.name, product.display_name))
                            elif product.id in period.product_ids.ids:
                                raise ValidationError(_(
                                    "Sorry, the selected sales person has a target at the same period ({}) and ({})"
                                    " Product is duplicated").format(
                                    period.name, product.display_name))
            if rec.date_to < rec.date_from:
                raise ValidationError(_("Date to must be greater than date from"))

    def _compute_check_close_date(self):
        for rec in self:
            rec.check_close_date = fields.Date.today() < rec.date_to

    def check_previous_data(self, target_achievement):
        self.ensure_one()
        vals = []
        commission_target_general_obj = self.env['sales.team.target.commissions']
        if target_achievement == 'confirmed_sale':
            orders = self.env['sale.order'].search([('user_id', '=', self.sales_person_id.id),
                                                    ('date_order', '>=', self.date_from),
                                                    ('date_order', '<=', self.date_to),
                                                    ('state', '=', 'sale')]).order_line
        elif target_achievement == 'invoice':
            orders = self.env['account.move'].search([('user_id', '=', self.sales_person_id.id),
                                                      ('invoice_date', '>=', self.date_from),
                                                      ('invoice_date', '<=', self.date_to),
                                                      ('state', '=', 'posted'),
                                                      ('payment_state', '!=', 'paid')]).invoice_line_ids
        elif target_achievement == 'paid_invoice':
            orders = self.env['account.move'].search([('user_id', '=', self.sales_person_id.id),
                                                      ('invoice_date', '>=', self.date_from),
                                                      ('invoice_date', '<=', self.date_to),
                                                      ('payment_state', '=', 'paid')]).invoice_line_ids
        else:
            orders = False
        if orders:
            for line in orders:
                if target_achievement == 'confirmed_sale':
                    vals.append({
                        'name': line.order_id.name,
                        'product_id': line.product_id.id,
                        'product_desc': line.name,
                        'uom_id': line.product_uom.id,
                        'quantity': line.product_uom_qty,
                        'price_subtotal': line.price_subtotal,
                        'price': line.price_unit,
                        'target_achievement': target_achievement,
                        'sale_order_line_id': line.id,
                        'target_commission_id': self.id,
                        'sale_id': line.order_id.id,
                        'is_commission': True
                    })
                elif target_achievement in ['invoice', 'paid_invoice']:
                    invoice_origin = self.env['sale.order'].search([('name', '=', line.move_id.invoice_origin)],
                                                                   limit=1)
                    if invoice_origin:
                        commissioned_products = self.env['sales.team.target.commissions'].search(
                            [('is_commission', '=', True),
                             ('sale_id', '=', invoice_origin.id)])
                    else:
                        commissioned_products = self.env['sales.team.target.commissions'].search(
                            [('is_commission', '=', True),
                             ('account_move_line_id', '=', line.id)])
                    if not commissioned_products:
                        vals.append({
                            'name': line.move_id.name,
                            'product_id': line.product_id.id,
                            'product_desc': line.name,
                            'uom_id': line.product_uom_id.id,
                            'quantity': line.quantity,
                            'price_subtotal': line.price_subtotal,
                            'price': line.price_unit,
                            'target_achievement': target_achievement,
                            'account_move_line_id': line.id,
                            'target_commission_id': self.id,
                            'sale_id': invoice_origin.id,
                            'is_commission': True
                        })
            commission_target_general_obj.create(vals)

    def run(self):
        for rec in self:
            rec.name = self.env['ir.sequence'].next_by_code('sales.target')
            # check if any previous data sales orders,invoices and delivery order
            rec.check_previous_data(self.target_achievement)
            rec.state = 'running'

    def close(self):
        for rec in self:
            rec.state = 'closed'

    def cancel(self):
        for rec in self:
            rec.state = 'canceled'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can't delete this record"))
        return super(SalesTeamTarget, self).unlink()
