from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DynamicApprovalLevel(models.Model):
    _inherit = 'dynamic.approval.level'

    role_id = fields.Many2one(
        comodel_name='dynamic.approval.role',
        string='Approver Role',
    )
    def _get_approver_source_field(self):
        """ append role_id in fields to check """
        res = super()._get_approver_source_field()
        res.append('role_id')
        return res

    @api.onchange('user_id', 'role_id')
    def _onchange_warn_user_and_role(self):
        """
        to allow to force use only one field user_id, role_id
        appear warning if user choose both fields
        """
        if self.user_id and self.role_id:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('User is high priority than role.\n'
                                 'If you choose both of them, system will ignore role!')}
            }

    def _get_approval_user(self, model, res):
        """ inherit to get user from role """
        rec = super()._get_approval_user(model, res)
        if not rec and self.role_id:
            rec = self.role_id.get_approval_user_role(approval=self.approval_id, model=model, res=res)
        return rec
