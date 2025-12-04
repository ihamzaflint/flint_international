from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'


    def export_bank_file_xlsx(self):
        data = {
            'batch_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        return self.env.ref('hr_payslip_batch_export.action_hr_payslip_export_wizard').report_action(self, data=data)

    def export_bank_file_xlsx_adjustments(self):
        data = {
            'batch_id': self.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        return self.env.ref('hr_payslip_batch_export.action_hr_payslip_export_wizard_adjustments').report_action(self, data=data)

