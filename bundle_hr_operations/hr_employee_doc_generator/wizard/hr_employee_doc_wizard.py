import xlrd
import base64
from odoo.exceptions import UserError
from odoo import fields, models, api
from datetime import timedelta


class HrEmployeeDocWizard(models.Model):
    _name = 'hr.employee.doc.wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hr Employee Document Wizard'

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=_default_employee_id)
    report_type = fields.Selection([
        ('embassy-male', 'Embassy Report'),
        ('job_offer', 'Job Offer Report'),

    ], string='Select Report Type', tracking=True, copy=False, required=True,)

    def get_report(self):
        self = self.sudo()
        for qweb in self:
            if qweb.report_type == 'embassy-male':
                return self.env.ref('hr_employee_doc_generator.embassy-male_qweb_report').report_action(self)