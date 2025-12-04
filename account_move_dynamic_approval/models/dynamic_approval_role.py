from odoo import _, models
from odoo.exceptions import UserError


class DynamicApprovalRole(models.Model):
    _inherit = 'dynamic.approval.role'

    def get_approval_user_role(self, approval, model, res):
        """ return approval user
            this function can be overridden to add custom users based on each model
        """
        rec = super().get_approval_user_role(approval, model, res)
        if model == 'account.move' and res.vertical_analytic_account_id and \
                res.vertical_analytic_account_id.apply_approval_role:
            analytic_approval_role = res.vertical_analytic_account_id.approval_role_ids.filtered(
                lambda line: line.role_id.id == self.id)
            msg = _('No user assigned to role %s in approval %s!') % (self.id, approval.display_name)
            if analytic_approval_role:
                user = analytic_approval_role.get_approve_user(approval, model, res)
                if user:
                    return user
                else:
                    raise UserError(msg)
            else:
                raise UserError(msg)
        return rec
