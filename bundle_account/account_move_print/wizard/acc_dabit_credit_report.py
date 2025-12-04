from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccDabitCreditReport(models.TransientModel):
    _name = "acc.debit.credit.report"
    _description = 'Acc Dabit Credit Report'

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @api.constrains('start_date', 'end_date')
    def _check_date_constraints(self):
        for rec in self:
            if rec.start_date > rec.end_date:
                raise UserError(_("Start date cannot be greater than end date."))
            if rec.end_date > fields.Date.today():
                raise UserError(_("End date cannot be greater than today's date."))

    def export_report(self):
        data = {
            'start_date': self.start_date, 'end_date':self.end_date
        }
        moves = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
        ])
        if not moves:
            raise UserError(_("No journal entries found form %s to %s" %(self.start_date, self.end_date)))
        
        report_action =  self.env.ref('account_move_print.action_print_acc_debit_credit_report').report_action(self, data=data)
        report_action.update({'close_on_report_download': True})
        return report_action


