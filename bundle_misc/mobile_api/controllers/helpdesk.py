import json
import logging
import base64
from datetime import datetime, timedelta

from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

from .main import MobileAPIController, validate_token, rate_limit

_logger = logging.getLogger(__name__)

class HelpdeskController(MobileAPIController):
    """Controller for helpdesk-related endpoints"""
    
    @http.route('/api/mobile/helpdesk/tickets', type='http', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def get_tickets(self):
        """Get list of tickets with pagination, sorting and filtering"""
        try:
            # Get query parameters
            limit = min(int(request.params.get('limit', 20)), 100)  # Max 100 records per page
            offset = int(request.params.get('offset', 0))
            sort_field = request.params.get('sort', 'create_date')
            sort_order = request.params.get('order', 'desc')
            status_filter = request.params.get('status')  # open, closed, all
            search = request.params.get('search', '')
            team_id = request.params.get('team_id')
            
            # Validate sort field to prevent SQL injection
            valid_sort_fields = ['create_date', 'write_date', 'priority', 'name', 'stage_id']
            if sort_field not in valid_sort_fields:
                sort_field = 'create_date'
                
            # Build domain
            domain = []
            
            # Filter by user's companies
            company = self._get_company_from_request()
            domain.append(('company_id', '=', company.id))
            
            # Filter by status
            if status_filter == 'open':
                domain.append(('stage_id.is_close', '=', False))
            elif status_filter == 'closed':
                domain.append(('stage_id.is_close', '=', True))
                
            # Filter by team
            if team_id and team_id.isdigit():
                domain.append(('team_id', '=', int(team_id)))
                
            # Filter by search term
            if search:
                domain.append('|')
                domain.append(('name', 'ilike', search))
                domain.append(('description', 'ilike', search))
                
            # Get tickets
            tickets = request.env['helpdesk.ticket'].with_context(company_id=company.id).search(
                domain,
                limit=limit,
                offset=offset,
                order=f"{sort_field} {sort_order}"
            )
            
            # Count total records for pagination
            total_count = request.env['helpdesk.ticket'].with_context(company_id=company.id).search_count(domain)
            
            # Format response
            result = {
                'tickets': [{
                    'id': ticket.id,
                    'name': ticket.name,
                    'description': ticket.description,
                    'priority': ticket.priority,
                    'priority_name': dict(ticket._fields['priority'].selection).get(ticket.priority),
                    'stage_id': ticket.stage_id.id,
                    'stage_name': ticket.stage_id.name,
                    'team_id': ticket.team_id.id,
                    'team_name': ticket.team_id.name,
                    'user_id': ticket.user_id.id,
                    'user_name': ticket.user_id.name if ticket.user_id else False,
                    'partner_id': ticket.partner_id.id,
                    'partner_name': ticket.partner_id.name if ticket.partner_id else False,
                    'create_date': ticket.create_date.isoformat(),
                    'write_date': ticket.write_date.isoformat(),
                    'last_app_sync_date': ticket.last_app_sync_date.isoformat() if ticket.last_app_sync_date else False,
                    'mobile_sync_status': ticket.mobile_sync_status,
                    'is_closed': ticket.stage_id.is_close,
                    'has_attachments': bool(ticket.attachment_ids),
                    'attachment_count': len(ticket.attachment_ids),
                } for ticket in tickets],
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count,
                }
            }
            
            # Mark tickets as synced
            tickets.with_context(company_id=company.id).write({
                'last_app_sync_date': fields.Datetime.now(),
                'mobile_sync_status': 'synced',
            })
            
            return self._json_response(result)
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/tickets/<int:ticket_id>', type='http', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def get_ticket(self, ticket_id):
        """Get detailed information for a specific ticket"""
        try:
            company = self._get_company_from_request()
            
            # Get ticket
            ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id).browse(ticket_id)
            
            # Check if ticket exists and user has access
            if not ticket.exists():
                return self._json_response({'error': 'Ticket not found'}, status=404)
                
            # Get ticket messages (mail.message)
            messages = request.env['mail.message'].search([
                ('model', '=', 'helpdesk.ticket'),
                ('res_id', '=', ticket.id),
                ('message_type', 'in', ['comment', 'notification']),
            ], order='create_date DESC', limit=50)
            
            # Get ticket attachments
            attachments = request.env['ir.attachment'].search([
                ('res_model', '=', 'helpdesk.ticket'),
                ('res_id', '=', ticket.id),
            ], order='create_date DESC')
            
            # Format response
            result = {
                'ticket': {
                    'id': ticket.id,
                    'name': ticket.name,
                    'description': ticket.description,
                    'priority': ticket.priority,
                    'priority_name': dict(ticket._fields['priority'].selection).get(ticket.priority),
                    'stage_id': ticket.stage_id.id,
                    'stage_name': ticket.stage_id.name,
                    'team_id': ticket.team_id.id,
                    'team_name': ticket.team_id.name,
                    'user_id': ticket.user_id.id,
                    'user_name': ticket.user_id.name if ticket.user_id else False,
                    'partner_id': ticket.partner_id.id,
                    'partner_name': ticket.partner_id.name if ticket.partner_id else False,
                    'create_date': ticket.create_date.isoformat(),
                    'write_date': ticket.write_date.isoformat(),
                    'last_app_sync_date': ticket.last_app_sync_date.isoformat() if ticket.last_app_sync_date else False,
                    'mobile_sync_status': ticket.mobile_sync_status,
                    'is_closed': ticket.stage_id.is_close,
                    'company_id': ticket.company_id.id,
                    'company_name': ticket.company_id.name,
                },
                'messages': [{
                    'id': message.id,
                    'body': message.body,
                    'author_id': message.author_id.id,
                    'author_name': message.author_id.name if message.author_id else _('System'),
                    'create_date': message.create_date.isoformat(),
                    'message_type': message.message_type,
                } for message in messages],
                'attachments': [{
                    'id': attachment.id,
                    'name': attachment.name,
                    'mimetype': attachment.mimetype,
                    'file_size': attachment.file_size,
                    'create_date': attachment.create_date.isoformat(),
                    'url': f'/api/mobile/helpdesk/attachment/{attachment.id}',
                } for attachment in attachments],
            }
            
            # Mark ticket as synced
            ticket.with_context(company_id=company.id).write({
                'last_app_sync_date': fields.Datetime.now(),
                'mobile_sync_status': 'synced',
            })
            
            return self._json_response(result)
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/tickets', type='json', auth='none', methods=['POST'], csrf=False)
    @validate_token
    def create_ticket(self):
        """Create a new ticket"""
        try:
            data = request.jsonrequest
            company = self._get_company_from_request()
            
            # Required fields
            name = data.get('name')
            description = data.get('description')
            
            if not name:
                return self._json_response({'error': 'Ticket name is required'}, status=400)
                
            # Optional fields
            team_id = data.get('team_id')
            priority = data.get('priority')
            partner_id = data.get('partner_id')
            mobile_local_id = data.get('mobile_local_id')
            
            # Prepare ticket values
            ticket_vals = {
                'name': name,
                'description': description,
                'company_id': company.id,
                'mobile_sync_status': 'synced',
                'last_app_sync_date': fields.Datetime.now(),
                'mobile_local_id': mobile_local_id,
            }
            
            # Add optional fields if provided
            if team_id:
                ticket_vals['team_id'] = int(team_id)
            if priority:
                ticket_vals['priority'] = priority
            if partner_id:
                ticket_vals['partner_id'] = int(partner_id)
                
            # Create ticket
            ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id).create(ticket_vals)
            
            # Handle attachments if provided
            attachments = []
            if data.get('attachments'):
                for attachment_data in data.get('attachments'):
                    try:
                        attachment_name = attachment_data.get('name')
                        attachment_data_base64 = attachment_data.get('data')
                        attachment_type = attachment_data.get('type', 'application/octet-stream')
                        
                        if attachment_name and attachment_data_base64:
                            attachment = request.env['ir.attachment'].with_context(company_id=company.id).create({
                                'name': attachment_name,
                                'datas': attachment_data_base64,
                                'res_model': 'helpdesk.ticket',
                                'res_id': ticket.id,
                                'type': 'binary',
                                'mimetype': attachment_type,
                                'company_id': company.id,
                            })
                            attachments.append({
                                'id': attachment.id,
                                'name': attachment.name,
                                'mimetype': attachment.mimetype,
                                'file_size': attachment.file_size,
                                'create_date': attachment.create_date.isoformat(),
                                'url': f'/api/mobile/helpdesk/attachment/{attachment.id}',
                            })
                    except Exception as e:
                        _logger.error(f"Failed to create attachment: {str(e)}")
            
            # Return created ticket
            return self._json_response({
                'ticket': {
                    'id': ticket.id,
                    'name': ticket.name,
                    'description': ticket.description,
                    'priority': ticket.priority,
                    'priority_name': dict(ticket._fields['priority'].selection).get(ticket.priority),
                    'stage_id': ticket.stage_id.id,
                    'stage_name': ticket.stage_id.name,
                    'team_id': ticket.team_id.id,
                    'team_name': ticket.team_id.name if ticket.team_id else False,
                    'user_id': ticket.user_id.id if ticket.user_id else False,
                    'user_name': ticket.user_id.name if ticket.user_id else False,
                    'partner_id': ticket.partner_id.id if ticket.partner_id else False,
                    'partner_name': ticket.partner_id.name if ticket.partner_id else False,
                    'create_date': ticket.create_date.isoformat(),
                    'write_date': ticket.write_date.isoformat(),
                    'last_app_sync_date': ticket.last_app_sync_date.isoformat() if ticket.last_app_sync_date else False,
                    'mobile_sync_status': ticket.mobile_sync_status,
                    'is_closed': ticket.stage_id.is_close,
                    'mobile_local_id': ticket.mobile_local_id,
                    'company_id': ticket.company_id.id,
                    'company_name': ticket.company_id.name,
                },
                'attachments': attachments,
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/tickets/<int:ticket_id>', type='json', auth='none', methods=['PUT'], csrf=False)
    @validate_token
    def update_ticket(self, ticket_id):
        """Update an existing ticket"""
        try:
            data = request.jsonrequest
            company = self._get_company_from_request()
            
            # Get ticket
            ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id).browse(ticket_id)
            
            # Check if ticket exists and user has access
            if not ticket.exists():
                return self._json_response({'error': 'Ticket not found'}, status=404)
                
            # Prepare update values
            update_vals = {}
            
            # Update fields if provided
            if 'name' in data:
                update_vals['name'] = data['name']
            if 'description' in data:
                update_vals['description'] = data['description']
            if 'priority' in data:
                update_vals['priority'] = data['priority']
            if 'stage_id' in data:
                update_vals['stage_id'] = int(data['stage_id'])
            if 'team_id' in data:
                update_vals['team_id'] = int(data['team_id'])
            if 'user_id' in data:
                update_vals['user_id'] = int(data['user_id']) if data['user_id'] else False
            if 'partner_id' in data:
                update_vals['partner_id'] = int(data['partner_id']) if data['partner_id'] else False
                
            # Always update sync status
            update_vals['mobile_sync_status'] = 'synced'
            update_vals['last_app_sync_date'] = fields.Datetime.now()
            
            # Update ticket
            ticket.with_context(company_id=company.id).write(update_vals)
            
            # Add message if provided
            if data.get('message'):
                ticket.with_context(company_id=company.id).message_post(
                    body=data['message'],
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                
            # Handle attachments if provided
            attachments = []
            if data.get('attachments'):
                for attachment_data in data.get('attachments'):
                    try:
                        attachment_name = attachment_data.get('name')
                        attachment_data_base64 = attachment_data.get('data')
                        attachment_type = attachment_data.get('type', 'application/octet-stream')
                        
                        if attachment_name and attachment_data_base64:
                            attachment = request.env['ir.attachment'].with_context(company_id=company.id).create({
                                'name': attachment_name,
                                'datas': attachment_data_base64,
                                'res_model': 'helpdesk.ticket',
                                'res_id': ticket.id,
                                'type': 'binary',
                                'mimetype': attachment_type,
                                'company_id': company.id,
                            })
                            attachments.append({
                                'id': attachment.id,
                                'name': attachment.name,
                                'mimetype': attachment.mimetype,
                                'file_size': attachment.file_size,
                                'create_date': attachment.create_date.isoformat(),
                                'url': f'/api/mobile/helpdesk/attachment/{attachment.id}',
                            })
                    except Exception as e:
                        _logger.error(f"Failed to create attachment: {str(e)}")
            
            # Get updated ticket
            updated_ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id).browse(ticket_id)
            
            # Notify mobile users about ticket update
            if updated_ticket.stage_id != ticket.stage_id:
                message = _("Ticket '%s' has been moved to stage '%s'") % (updated_ticket.name, updated_ticket.stage_id.name)
                updated_ticket._notify_mobile_users(message, include_customer=True)
            
            # Return updated ticket
            return self._json_response({
                'ticket': {
                    'id': updated_ticket.id,
                    'name': updated_ticket.name,
                    'description': updated_ticket.description,
                    'priority': updated_ticket.priority,
                    'priority_name': dict(updated_ticket._fields['priority'].selection).get(updated_ticket.priority),
                    'stage_id': updated_ticket.stage_id.id,
                    'stage_name': updated_ticket.stage_id.name,
                    'team_id': updated_ticket.team_id.id,
                    'team_name': updated_ticket.team_id.name if updated_ticket.team_id else False,
                    'user_id': updated_ticket.user_id.id if updated_ticket.user_id else False,
                    'user_name': updated_ticket.user_id.name if updated_ticket.user_id else False,
                    'partner_id': updated_ticket.partner_id.id if updated_ticket.partner_id else False,
                    'partner_name': updated_ticket.partner_id.name if updated_ticket.partner_id else False,
                    'create_date': updated_ticket.create_date.isoformat(),
                    'write_date': updated_ticket.write_date.isoformat(),
                    'last_app_sync_date': updated_ticket.last_app_sync_date.isoformat() if updated_ticket.last_app_sync_date else False,
                    'mobile_sync_status': updated_ticket.mobile_sync_status,
                    'is_closed': updated_ticket.stage_id.is_close,
                    'company_id': updated_ticket.company_id.id,
                    'company_name': updated_ticket.company_id.name,
                },
                'new_attachments': attachments,
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/tickets/<int:ticket_id>/message', type='json', auth='none', methods=['POST'], csrf=False)
    @validate_token
    def add_ticket_message(self, ticket_id):
        """Add a message to a ticket"""
        try:
            data = request.jsonrequest
            company = self._get_company_from_request()
            
            # Get ticket
            ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id).browse(ticket_id)
            
            # Check if ticket exists and user has access
            if not ticket.exists():
                return self._json_response({'error': 'Ticket not found'}, status=404)
                
            # Get message content
            message = data.get('message')
            
            if not message:
                return self._json_response({'error': 'Message content is required'}, status=400)
                
            # Post message
            message_id = ticket.with_context(company_id=company.id).message_post(
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            
            # Handle attachments if provided
            attachments = []
            if data.get('attachments'):
                for attachment_data in data.get('attachments'):
                    try:
                        attachment_name = attachment_data.get('name')
                        attachment_data_base64 = attachment_data.get('data')
                        attachment_type = attachment_data.get('type', 'application/octet-stream')
                        
                        if attachment_name and attachment_data_base64:
                            attachment = request.env['ir.attachment'].with_context(company_id=company.id).create({
                                'name': attachment_name,
                                'datas': attachment_data_base64,
                                'res_model': 'mail.message',
                                'res_id': message_id.id,
                                'type': 'binary',
                                'mimetype': attachment_type,
                                'company_id': company.id,
                            })
                            attachments.append({
                                'id': attachment.id,
                                'name': attachment.name,
                                'mimetype': attachment.mimetype,
                                'file_size': attachment.file_size,
                                'create_date': attachment.create_date.isoformat(),
                                'url': f'/api/mobile/helpdesk/attachment/{attachment.id}',
                            })
                    except Exception as e:
                        _logger.error(f"Failed to create attachment: {str(e)}")
            
            # Return message
            return self._json_response({
                'message': {
                    'id': message_id.id,
                    'body': message_id.body,
                    'author_id': message_id.author_id.id,
                    'author_name': message_id.author_id.name,
                    'create_date': message_id.create_date.isoformat(),
                    'message_type': message_id.message_type,
                },
                'attachments': attachments,
            })
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/attachment/<int:attachment_id>', type='http', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def get_attachment(self, attachment_id):
        """Get attachment content"""
        try:
            company = self._get_company_from_request()
            
            # Get attachment
            attachment = request.env['ir.attachment'].with_context(company_id=company.id).browse(attachment_id)
            
            # Check if attachment exists and user has access
            if not attachment.exists():
                return self._json_response({'error': 'Attachment not found'}, status=404)
                
            # Check if attachment belongs to a helpdesk ticket or message
            if attachment.res_model not in ['helpdesk.ticket', 'mail.message']:
                return self._json_response({'error': 'Attachment not accessible'}, status=403)
                
            # If attachment belongs to a message, check if message belongs to a ticket
            if attachment.res_model == 'mail.message':
                message = request.env['mail.message'].browse(attachment.res_id)
                if message.model != 'helpdesk.ticket':
                    return self._json_response({'error': 'Attachment not accessible'}, status=403)
            
            # Return attachment content
            return http.request.make_response(
                base64.b64decode(attachment.datas),
                headers=[
                    ('Content-Type', attachment.mimetype),
                    ('Content-Disposition', f'attachment; filename={attachment.name}'),
                    ('Content-Length', str(attachment.file_size)),
                ]
            )
            
        except Exception as e:
            return self._handle_exception(e)
    
    @http.route('/api/mobile/helpdesk/options', type='http', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def get_helpdesk_options(self):
        """Get helpdesk configuration options"""
        try:
            company = self._get_company_from_request()
            
            # Get options
            ticket = request.env['helpdesk.ticket'].with_context(company_id=company.id)
            
            result = {
                'priorities': ticket.get_ticket_priority_options(),
                'stages': ticket.get_ticket_stage_options(),
                'teams': ticket.get_ticket_team_options(),
                'types': ticket.get_ticket_type_options(),
            }
            
            return self._json_response(result)
            
        except Exception as e:
            return self._handle_exception(e)
