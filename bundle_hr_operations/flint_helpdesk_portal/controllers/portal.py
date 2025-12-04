from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError
import base64


class HelpdeskPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            values['ticket_count'] = request.env['helpdesk.ticket'].search_count([])
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        
        # Add create ticket button
        values.update({
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'create_ticket_url': '/my/helpdesk/ticket/create'
        })
        return request.render("helpdesk.portal_helpdesk_ticket", values)

    @http.route(['/my/helpdesk/ticket/create'], type='http', auth="user", website=True)
    def portal_create_ticket(self, **kw):
        ticket_types = request.env['helpdesk.ticket.type'].sudo().search([])
        service_types = request.env['service.type'].sudo().search([])
        
        values = {
            'ticket_types': ticket_types,
            'service_types': service_types,
            'page_name': 'create_ticket',
            'default_url': '/my/helpdesk/ticket/create',
            'error': {},
            'error_message': [],
        }
        return request.render("flint_helpdesk_portal.portal_create_ticket", values)

    @http.route(['/helpdesk/ticket/submit'], type='http', auth="user", website=True, methods=['POST'])
    def submit_ticket(self, **kwargs):
        try:
            # Get current user's employee record
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
            if not employee:
                return self.portal_create_ticket(**kwargs)

            # Handle multiple service types
            service_type_ids = request.httprequest.form.getlist('service_type_ids')
            if not service_type_ids:
                raise ValidationError(_('Please select at least one service type.'))

            # Get sequence for ticket name
            name = request.env['ir.sequence'].sudo().next_by_code('helpdesk.ticket') or _('New')

            # Get default support team
            team = request.env['helpdesk.team'].sudo().search([('use_website_helpdesk_form', '=', True)], limit=1)
            if not team:
                raise ValidationError(_('No support team is configured for web tickets. Please contact your administrator.'))

            ticket_values = {
                'team_id': team.id,
                'name': name,
                'ticket_type_id': int(kwargs['ticket_type_id']),
                'service_type_ids': [(6, 0, [int(st_id) for st_id in service_type_ids])],
                'description': kwargs['description'],
                'partner_id': request.env.user.partner_id.id,
                'employee_id': employee.id,
            }

            # Add employee details if fields exist
            if hasattr(employee, 'registration_number'):
                ticket_values['registration_number'] = employee.registration_number
            if hasattr(employee, 'project_id'):
                ticket_values['project_id'] = employee.project_id.id if employee.project_id else False
            if hasattr(employee, 'iqama_number'):
                ticket_values['iqama_no'] = employee.iqama_number
            if hasattr(employee, 'visa_expire'):
                ticket_values['visa_expire'] = employee.visa_expire
            elif hasattr(employee, 'expiry_date_iqama'):
                ticket_values['visa_expire'] = employee.expiry_date_iqama
            if employee.work_email:
                ticket_values['email'] = employee.work_email
            if employee.work_phone:
                ticket_values['phone'] = employee.work_phone

            # Create ticket first
            ticket = request.env['helpdesk.ticket'].sudo().create(ticket_values)

            # Handle approval attachment if uploaded
            approval_attachment = request.httprequest.files.get('approval_attachment')
            if approval_attachment:
                attachment_value = {
                    'name': approval_attachment.filename,
                    'datas': base64.b64encode(approval_attachment.read()),
                    'res_model': 'helpdesk.ticket',
                    'res_id': ticket.id,
                    'type': 'binary',
                    'description': 'Approval Document',
                }
                request.env['ir.attachment'].sudo().create(attachment_value)

            return request.redirect('/my/tickets')
        except ValidationError as e:
            values = self._prepare_portal_layout_values()
            values.update({
                'error_message': str(e),
                'kwargs': kwargs,
                'ticket_types': request.env['helpdesk.ticket.type'].search([]),
                'service_types': request.env['service.type'].sudo().search([]),
            })
            return request.render("flint_helpdesk_portal.portal_create_ticket", values)
        except Exception as e:
            values = self._prepare_portal_layout_values()
            values.update({
                'error_message': _("An error occurred while creating the ticket. Please try again."),
                'kwargs': kwargs,
                'ticket_types': request.env['helpdesk.ticket.type'].search([]),
                'service_types': request.env['service.type'].sudo().search([]),
            })
            return request.render("flint_helpdesk_portal.portal_create_ticket", values)

    @http.route(['/helpdesk/get_service_types'], type='json', auth="user", website=True)
    def get_service_types(self, service_category_id=None):
        if not service_category_id:
            return []
        
        service_types = request.env['service.type'].sudo().search([
            ('helpdesk_type_id', '=', int(service_category_id))
        ])
        return [{'id': st.id, 'name': st.name} for st in service_types]

    @http.route(['/helpdesk/ticket/post_message'], type='http', auth="user", website=True, methods=['POST'])
    def post_ticket_message(self, **kwargs):
        ticket_id = kwargs.get('ticket_id')
        message = kwargs.get('message')
        
        if not ticket_id or not message:
            return request.redirect('/my/tickets')
            
        try:
            ticket = request.env['helpdesk.ticket'].sudo().browse(int(ticket_id))
            # Check if user has access to this ticket
            if ticket.exists() and (ticket.partner_id.id == request.env.user.partner_id.id):
                ticket.message_post(
                    body=message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        except Exception as e:
            return request.redirect('/my/tickets')
            
        return request.redirect('/my/ticket/%s' % ticket_id)

    @http.route(['/my/ticket/<int:ticket_id>'], type='http', auth="user", website=True)
    def portal_my_ticket(self, ticket_id, **kw):
        ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
        
        if not ticket.exists():
            return request.not_found()
            
        values = {
            'page_name': 'ticket',
            'ticket': ticket,
            'user': request.env.user,
            'res_id': ticket.id,
            'res_model': 'helpdesk.ticket',
            # Message thread values
            'pid': request.env.user.partner_id.id,
            'hash': kw.get('hash', ''),
            'token': ticket.access_token if hasattr(ticket, 'access_token') else '',
            'message': kw.get('message', ''),
            'message_attachment_id': kw.get('message_attachment_id', ''),
            'partner_id': request.env.user.partner_id.id,
        }
        
        return request.render("flint_helpdesk_portal.portal_my_ticket", values)
