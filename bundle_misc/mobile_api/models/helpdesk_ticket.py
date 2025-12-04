from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    last_app_sync_date = fields.Datetime(
        string='Last Mobile Sync',
        readonly=True,
        help='Last time this ticket was synced with the mobile app'
    )
    mobile_sync_status = fields.Selection([
        ('pending', 'Pending Sync'),
        ('synced', 'Synced'),
        ('failed', 'Sync Failed'),
    ], string='Mobile Sync Status', default='pending', copy=False)
    mobile_local_id = fields.Char(
        string='Mobile Local ID',
        copy=False,
        help='Temporary ID used by the mobile app for offline creation'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        groups='base.group_multi_company',
        help='Company this ticket belongs to'
    )
    
    def mark_as_synced(self):
        """Mark ticket as synced with mobile app"""
        self.ensure_one()
        return self.with_context(company_id=self.company_id.id).write({
            'last_app_sync_date': fields.Datetime.now(),
            'mobile_sync_status': 'synced',
        })
    
    def mark_as_pending_sync(self):
        """Mark ticket as pending sync with mobile app"""
        self.ensure_one()
        return self.with_context(company_id=self.company_id.id).write({
            'mobile_sync_status': 'pending',
        })
    
    @api.model
    def get_ticket_priority_options(self):
        """Return ticket priority options for mobile app"""
        return dict(self._fields['priority'].selection)
    
    @api.model
    def get_ticket_stage_options(self):
        """Return ticket stage options for mobile app"""
        stages = self.env['helpdesk.stage'].search([])
        return [{
            'id': stage.id,
            'name': stage.name,
            'sequence': stage.sequence,
            'is_close': stage.is_close,
        } for stage in stages]
    
    @api.model
    def get_ticket_team_options(self):
        """Return ticket team options for mobile app"""
        teams = self.env['helpdesk.team'].search([])
        return [{
            'id': team.id,
            'name': team.name,
        } for team in teams]
    
    @api.model
    def get_ticket_type_options(self):
        """Return ticket type options for mobile app"""
        types = self.env['helpdesk.ticket.type'].search([])
        return [{
            'id': type_id.id,
            'name': type_id.name,
        } for type_id in types]
    
    def _notify_mobile_users(self, message, include_customer=False):
        """Send notification to mobile users about ticket updates"""
        self.ensure_one()
        users_to_notify = self.env['res.users']
        
        # Always notify assigned user
        if self.user_id:
            users_to_notify |= self.user_id
            
        # Notify team members if configured
        if self.team_id and self.team_id.member_ids:
            users_to_notify |= self.team_id.member_ids
            
        # Notify customer if requested and exists
        if include_customer and self.partner_id and self.partner_id.user_ids:
            users_to_notify |= self.partner_id.user_ids
            
        # Find mobile users for these Odoo users
        mobile_users = self.env['mobile.user'].search([
            ('user_id', 'in', users_to_notify.ids),
            ('fcm_token', '!=', False),
            ('active', '=', True)
        ])
        
        if mobile_users:
            # In a real implementation, this would integrate with Firebase
            # to send actual push notifications
            _logger.info(
                f"Would send mobile notification about ticket {self.id} "
                f"to {len(mobile_users)} devices: {message}"
            )
            
        return True
