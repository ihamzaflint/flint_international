from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('sent_to_bank', 'Sent to Bank')], ondelete={'sent_to_bank': 'cascade'})
    saib_payroll_count = fields.Integer(compute='_compute_saib_payroll_count', string='SAIB Payroll Count')
    saib_payment_id = fields.Many2one('saib.payroll', string='SAIB Payroll')
    is_saib_payment_sent = fields.Boolean(string='SAIB Payment Sent', compute='_compute_is_saib_payment_sent')
    regular_effective_date = fields.Date(string='Regular Payment Date', help='Effective date for regular payroll payment')
    adjustment_effective_date = fields.Date(string='Adjustment Payment Date', help='Effective date for adjustment allowances payment')

    # [sanjay-techvoot] Compute how many SAIB payroll records are linked to this payslip run.
    def _compute_saib_payroll_count(self):
        """Compute the number of SAIB payrolls linked to this batch"""
        for record in self:
            record.saib_payroll_count = self.env['saib.payroll'].search_count([('payslip_run_id', '=', record.id)])
    
    # [sanjay-techvoot] Open a window action showing SAIB payrolls linked to this payslip run.
    def action_view_saib_payrolls(self):
        """Open the SAIB payrolls linked to this batch"""
        self.ensure_one()
        payrolls = self.env['saib.payroll'].search([('payslip_run_id', '=', self.id)])
        
        action = {
            'name': _('SAIB Payrolls'),
            'type': 'ir.actions.act_window',
            'res_model': 'saib.payroll',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payrolls.ids)],
            'context': {'default_payslip_run_id': self.id},
        }
        
        # If there's only one payroll, open it directly in form view
        if len(payrolls) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = payrolls.id
        
        return action

    # [sanjay-techvoot] Create and send a SAIB payroll record for this payslip run to the bank.
    def action_send_to_saib(self):
        """Send payroll batch to SAIB bank"""
        self.ensure_one()

        if not self.slip_ids:
            raise UserError(_('No payslips found in this batch.'))

        if self.saib_payment_id:
            raise UserError(_('This batch has already been sent to SAIB bank.'))

        company = self.env.company
        if not company.mol_establishment_id:
            raise UserError(_('Please configure MOL Establishment ID in company settings before sending to SAIB bank.'))

        if not company.saib_bank_account_id:
            raise UserError(_('Please configure SAIB Bank Account in company settings before sending to SAIB bank.'))

        # Create SAIB payroll by calling the action_create_saib_payroll method
        result = self.action_create_saib_payroll()
        
        # Get the created payroll record
        saib_payroll = self.saib_payment_id
        
        # Send to bank
        saib_payroll.action_send_to_bank()

        # Return the view of the created payroll
        return {
            'type': 'ir.actions.act_window',
            'name': _('SAIB Payroll'),
            'res_model': 'saib.payroll',
            'res_id': saib_payroll.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # [sanjay-techvoot] Build a SAIB payroll record and its lines from this payslip run.
    def action_create_saib_payroll(self):
        """Create a SAIB payroll from this batch"""
        self.ensure_one()
        
        # Check if there are payslips in the batch
        if not self.slip_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('No payslips found in this batch.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Get MOL establishment ID from config or company
        mol_id = self.env.company.mol_establishment_id or self.env['ir.config_parameter'].sudo().get_param('saib_bank_integration.mol_establishment_id')
        if not mol_id:
            raise UserError(_('Please configure MOL Establishment ID in company settings or SAIB Bank settings.'))
            
        # Get company bank account
        company_bank = self.env.company.saib_bank_account_id or self.env['res.partner.bank'].search([
            ('partner_id', '=', self.company_id.partner_id.id),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not company_bank:
            raise UserError(_('Please configure a bank account for the company.'))
        
        # Create SAIB payroll
        currency = self.env.company.currency_id
        payroll_date = self.regular_effective_date or fields.Date.today()
        
        saib_payroll = self.env['saib.payroll'].create({
            'name': 'SAIB-' + self.name + '/Regular',  
            'payroll_date': payroll_date,
            'mol_establishment_id': mol_id,
            'currency_id': currency.id,
            'bank_account_id': company_bank.id,
            'payslip_run_id': self.id,
        })
        
        # Populate payroll lines
        line_count = 0
        for slip in self.slip_ids.filtered(lambda s: s.state in ['done', 'paid']):
            if not slip.employee_id or not slip.employee_id.bank_account_id:
                continue
                
            net_amount = sum(slip.line_ids.filtered(lambda l: l.code == 'NET').mapped('total'))
            if not net_amount:
                continue
                
            self.env['saib.payroll.line'].create({
                'payroll_id': saib_payroll.id,
                'employee_id': slip.employee_id.id,
                'amount': net_amount,
                'currency_id': self.company_id.currency_id.id,
                'bank_account': slip.employee_id.bank_account_id.acc_number
            })
            line_count += 1
        
        # Link the payroll to this batch
        self.write({
            'saib_payment_id': saib_payroll.id
        })
        
        return {
            'name': _('SAIB Payroll'),
            'type': 'ir.actions.act_window',
            'res_model': 'saib.payroll',
            'view_mode': 'form',
            'res_id': saib_payroll.id,
            'context': {'form_view_initial_mode': 'edit'},
        }

    # [sanjay-techvoot] Compute flag: True if a SAIB payroll is already linked to this payslip run.
    @api.depends('saib_payment_id')
    def _compute_is_saib_payment_sent(self):
        for record in self:
            record.is_saib_payment_sent = bool(record.saib_payment_id)
