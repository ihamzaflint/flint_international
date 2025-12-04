from odoo import models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_create_portal_user(self):
        """Create a portal user for the employee using their work email."""
        self.ensure_one()
        
        if not self.work_email:
            raise UserError(_("Work email is required to create a portal user."))
            
        if self.user_id:
            raise UserError(_("This employee already has a user account."))

        # Check for existing users or partners with the same email
        existing_user = self.env['res.users'].sudo().search([
            '|',
            ('login', '=', self.work_email),
            ('email', '=', self.work_email),
            ('active', 'in', [True, False])  # Include inactive users
        ], limit=1)
        
        if existing_user:
            raise UserError(_(
                "A user with this email already exists (it might be archived). "
                "Please use a different email address or reactivate the existing user."
            ))

        existing_partner = self.env['res.partner'].sudo().search([
            ('email', '=', self.work_email),
        ], limit=1)
        
        if existing_partner:
            existing_partner.unlink()
        
        # Create user with portal access
        user_vals = {
            'name': self.name,
            'login': self.work_email,
            'email': self.work_email,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        }
        
        try:
            user = self.env['res.users'].sudo().create(user_vals)
            self.user_id = user.id
            
            # Create partner if doesn't exist
            if not self.address_id:
                partner = self.env['res.partner'].sudo().create({
                    'name': self.name,
                    'email': self.work_email,
                    'password': '123',
                    'type': 'private',
                    'phone': self.work_phone,
                    'mobile': self.work_phone,
                })
                self.address_id = partner.id
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Portal user created successfully with password: 123'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error("Error creating portal user: %s", str(e))
            raise UserError(_("Failed to create portal user: %s") % str(e))
