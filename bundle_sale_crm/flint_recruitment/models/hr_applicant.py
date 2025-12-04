from odoo import models, fields, api


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    is_accepted = fields.Boolean(string='Is Accepted', default=False,related='stage_id.hired_stage',store=True)