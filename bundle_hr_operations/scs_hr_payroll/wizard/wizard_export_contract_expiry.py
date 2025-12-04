from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class WizardExportContractExpiry(models.TransientModel):
    _name = 'wizard.export.contract.expiry'
    _description = 'Wizard Export Contract Expiry'

    # name = fields.Char(string="Name")

    def export_report(self):
        contract_ids = self.env['hr.contract'].search(
            [
                ("date_end", ">=", fields.Date.today()),
                ("date_end", "<=", fields.Date.today() + relativedelta(months=+3)),
            ],
            order="date_end",
        )
        if not contract_ids:
            raise UserError(_("No Contract Details Found"))
        data = {
            'contract_ids': contract_ids.ids
        }
        return self.env.ref('scs_hr_payroll.action_contract_expire_export_wizard').report_action(self, data=data)
