from odoo import models, fields

class SaibBankStatementLine(models.Model):
    _name = 'saib.bank.statement.line'
    _description = 'SAIB Bank Statement Line'

    statement_id = fields.Many2one('saib.bank.statement', string='Statement')
    date = fields.Date('Date', required=True)
    name = fields.Char('Description')
    ref = fields.Char('Reference')
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Monetary('Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
                
