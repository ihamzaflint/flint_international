from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class WizardExportIqama(models.TransientModel):
    _name = 'wizard.export.iqama'
    _description = 'Wizard Export Iqama'

    # name = fields.Char(string="Name")

    def export_report(self):
        employee_ids = self.env['hr.employee'].search(
            [
                ("visa_expire", ">=", fields.Date.today()),
                ("visa_expire", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="visa_expire",
        )
        if not employee_ids:
            raise UserError(_("No Employee Found"))
        data = {
            'employee_ids': employee_ids.ids
        }
        return self.env.ref('scs_hr_payroll.action_iqama_expire_export_wizard').report_action(self, data=data)
