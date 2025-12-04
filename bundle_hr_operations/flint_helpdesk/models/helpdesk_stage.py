from odoo import fields, models


class HelpDeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    under_approval = fields.Boolean(string='Under Approval', default=False)
    is_draft = fields.Boolean(string='Is Draft', default=False)
    is_closed = fields.Boolean(string='Is Closed', default=False)
    in_progress = fields.Boolean(string='In Progress', default=False)
    is_operation_manager_reject = fields.Boolean(string='Operation manager rejected', default=False)
    is_on_hold = fields.Boolean(string='Is On Hold', default=False)