from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    mol_establishment_id = fields.Char('MOL Establishment ID', 
        help='Ministry of Labor Establishment ID required for WPS payroll processing')
    saib_bank_account_id = fields.Many2one('res.partner.bank', string='SAIB Bank Account',
        help='Bank account used for SAIB payroll processing')
