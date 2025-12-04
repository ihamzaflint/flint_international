from odoo import models, fields, api


class ApplicantLineReject(models.Model):
    _name = "applicant.line.reject"
    _description = "Rejected Applicant Line"

    applicant_id = fields.Many2one('applicant.line', string="Applicant", required=True, ondelete='cascade')
    rejection_date = fields.Date(string="Rejection Date", required=True)
    reason = fields.Text(string="Rejection Reason")
