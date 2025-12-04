from odoo import fields, models, api


class HrApplicantRefuseReason(models.Model):
    _inherit = 'hr.applicant.refuse.reason'

    is_applicant_refuse = fields.Boolean()
