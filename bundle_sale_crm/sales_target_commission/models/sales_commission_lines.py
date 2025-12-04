from odoo import api, fields, models


class CommissionCommissionsLines(models.Model):
    _name = 'sales.commission.lines'
    _rec_name = 'sales_commission_reference'

    sales_commission_reference = fields.Char(string="Sales commission reference")
    commission_date = fields.Date(string="Commission Date")
    sales_team_id = fields.Many2one('crm.team', string="Sales Team")
    user_id = fields.Many2one('res.users', string="Sales Person")
    commission_percentage = fields.Float(string="commission Percentage")
    amount = fields.Float(string="Commission Amount")
    currency_id = fields.Many2one('res.currency', string="Currency")
    amount_in_company_currency = fields.Float(string="Amount in company currency")
    commission_lines_ids = fields.One2many('sales.team.target.commissions', 'sales_commission_line_id',
                                           string="Sales Commissions Lines")
    target_id = fields.Many2one('sales.team.target', string="Target")
    amount_total = fields.Float(string="Total", compute='compute_total_amount')

    @api.depends('commission_lines_ids', 'commission_lines_ids.price_subtotal')
    def compute_total_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.commission_lines_ids.mapped('price_subtotal'))
