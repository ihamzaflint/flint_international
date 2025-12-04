from odoo import api, fields, models

class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Hr Employee Document Generator"

    @api.model
    def _default_employee_id(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True, default=_default_employee_id)
    report_type = fields.Selection([
        ('embassy-male', 'Embassy-male Report'),
        ('job_offer', 'Job Offer Report'),

    ], string='Select Report Type', tracking=True, copy=False, required=True,)

    def get_selected_report(self):
        for qweb in self:
            if qweb.report_type == 'embassy-male':
                return self.env.ref('hr_employee_doc_generator.embassy-male_qweb_report').report_action(self)