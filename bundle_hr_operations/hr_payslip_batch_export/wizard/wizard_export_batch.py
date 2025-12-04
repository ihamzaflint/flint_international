from odoo import api, fields, models

class WizardExportBatch(models.TransientModel):
    _name = 'wizard.export.batch'
    _description = 'Wizard Export Batch'

    # name = fields.Char(string="Name")

    def export_report(self):
        data = {
            'batch_id': self._context.get('active_id')
        }
        return self.env.ref('hr_payslip_batch_export.action_hr_payslip_export_wizard').report_action(self, data=data)
