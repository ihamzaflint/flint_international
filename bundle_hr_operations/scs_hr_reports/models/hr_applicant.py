from odoo import models, fields, api


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    file_number = fields.Char("File Number")
    basic_monthly_sal = fields.Float("Basic Monthly Salary")
    housing_alw = fields.Float("Housing Allowance")
    transportation_alw = fields.Float("Transportation Allowance")
    contract_status = fields.Char("Contract Status")
    medical_care = fields.Char("Medical Care")
    vacation = fields.Char("Vacation")
    travel_ticket = fields.Char("Travel Ticket")
    probation_period = fields.Char("Probation Period")
    contract_duration = fields.Char("Contract Duration")
    work_location_id = fields.Many2one('hr.work.location', "Work Location")

    @api.onchange('job_id')
    def onchange_job_id(self):
        for rec in self:
            work_location_id = False
            if rec.job_id and rec.job_id.work_location_id:
                work_location_id = rec.job_id.work_location_id
            rec.work_location_id = work_location_id
