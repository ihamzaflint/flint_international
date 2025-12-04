from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaibBankStatement(models.Model):
    _name = 'saib.bank.statement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'SAIB Bank Statement'
    _order = 'date desc'

    name = fields.Char('Reference', required=True, readonly=True, default='New')
    date = fields.Date('Statement Date', required=True, tracking=True)
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, 
                                 default=lambda self: self.env.company.currency_id)
    opening_balance = fields.Monetary('Opening Balance', currency_field='currency_id', tracking=True)
    closing_balance = fields.Monetary('Closing Balance', currency_field='currency_id', tracking=True)
    total_debit = fields.Monetary('Total Debit', currency_field='currency_id', compute='_compute_totals', store=True)
    total_credit = fields.Monetary('Total Credit', currency_field='currency_id', compute='_compute_totals', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('saib.bank.statement.line', 'statement_id', string='Statement Lines')

    # [sanjay-techvoot] Auto-generate sequence for new statements if name is 'New'.
    # Ensures each statement gets a unique reference on create.
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('saib.bank.statement') or 'New'
        return super(SaibBankStatement, self).create(vals)

    # [sanjay-techvoot] Fetch statement from SAIB via API and process returned data.
    # Calls external API and raises UserError on failure.
    def action_fetch_statement(self):
        """Fetch statement from SAIB bank"""
        self.ensure_one()
        
        try:
            # Call SAIB API to get statement
            api = self.env['saib.api']
            endpoint = '/b2b/accounts/statements'
            data = {
                'accountNumber': self.account_id.acc_number,
                'fromDate': self.date_from.strftime('%Y-%m-%d'),
                'toDate': self.date_to.strftime('%Y-%m-%d'),
                'statementType': self.statement_type,
            }
            
            response = api._make_request('POST', endpoint, data)
            self._process_statement_data(response)
            
        except Exception as e:
            raise UserError(_('Failed to fetch statement from SAIB: %s') % str(e))
    
    # [sanjay-techvoot] Compute total debit and credit from statement lines.
    # Stores aggregated totals in total_debit and total_credit.
    @api.depends('line_ids.amount')
    def _compute_totals(self):
        for statement in self:
            statement.total_debit = abs(sum(statement.line_ids.filtered(lambda l: l.amount < 0).mapped('amount')))
            statement.total_credit = sum(statement.line_ids.filtered(lambda l: l.amount > 0).mapped('amount'))

    # [sanjay-techvoot] Mark statement as 'confirmed'.
    # Simple state transition.
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    # [sanjay-techvoot] Mark statement as 'posted'.
    # Simple state transition.
    def action_post(self):
        self.write({'state': 'posted'})

    # [sanjay-techvoot] Cancel statement unless already posted (raises error).
    # Prevents cancelling posted statements.
    def action_cancel(self):
        if self.state == 'posted':
            raise UserError(_('Cannot cancel a posted statement'))
        self.write({'state': 'cancelled'})

    # [sanjay-techvoot] Reset statement to draft unless posted (raises error).
    # Prevents resetting posted statements to draft.
    def action_draft(self):
        if self.state == 'posted':
            raise UserError(_('Cannot reset a posted statement to draft'))
        self.write({'state': 'draft'})


class SaibBankStatementLine(models.Model):
    _name = 'saib.bank.statement.line'
    _description = 'SAIB Bank Statement Line'
    _order = 'date, id'

    statement_id = fields.Many2one('saib.bank.statement', string='Statement', required=True, ondelete='cascade')
    date = fields.Date('Date', required=True)
    name = fields.Char('Description', required=True)
    ref = fields.Char('Reference')
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True,
                           help='Positive amount for credit, negative for debit')
    currency_id = fields.Many2one('res.currency', related='statement_id.currency_id', store=True)
    company_id = fields.Many2one('res.company', related='statement_id.company_id', store=True)
    transaction_type = fields.Selection([
        ('transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('payment', 'Payment'),
        ('fee', 'Bank Fee'),
        ('other', 'Other')
    ], string='Transaction Type', required=True, default='other')
    state = fields.Selection(related='statement_id.state', store=True)
