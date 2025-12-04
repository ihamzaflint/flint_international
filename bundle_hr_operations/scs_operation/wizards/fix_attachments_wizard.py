from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FixAttachmentsWizard(models.TransientModel):
    _name = 'fix.attachments.wizard'
    _description = 'Fix Orphaned Attachments Wizard'

    name = fields.Char(string='Name', default='Fix Orphaned Attachments', readonly=True)
    description = fields.Text(string='Description', default='This wizard will fix orphaned attachments that have res_id = 0 and link them to the correct employee records.', readonly=True)

    def action_fix_orphaned_attachments(self):
        """Fix all orphaned attachments in the system"""
        try:
            fixed_count = self.env['hr.employee']._fix_all_orphaned_attachments()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Fixed {} orphaned attachments successfully.').format(fixed_count),
                    'type': 'success',
                }
            }
        except Exception as e:
            raise UserError(_('Error fixing attachments: {}').format(str(e))) 