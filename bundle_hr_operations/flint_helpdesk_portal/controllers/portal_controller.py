from odoo import http
from odoo.http import request, Response
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
import os
import json
from calendar import monthrange
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo.fields import Date

def format_file_size(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

class HelpdeskPortalController(http.Controller):
    def _get_tickets_statistics(self):
        # Get all user tickets
        domain = [('partner_id', '=', request.env.user.partner_id.id)]
        tickets = request.env['helpdesk.ticket'].sudo().search(domain)
        
        # Status statistics
        status_count = defaultdict(int)
        for ticket in tickets:
            status_count[ticket.stage_id.name] += 1
        
        # Priority statistics
        priority_count = defaultdict(int)
        priority_map = {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High'
        }
        for ticket in tickets:
            priority_count[priority_map.get(str(ticket.priority), 'Low')] += 1
            
        # Monthly statistics
        today = datetime.today()
        last_6_months = [(today - timedelta(days=i*30)).strftime('%B') for i in range(5, -1, -1)]
        monthly_new = defaultdict(int)
        monthly_resolved = defaultdict(int)
        
        for ticket in tickets:
            month = ticket.create_date.strftime('%B')
            if month in last_6_months:
                monthly_new[month] += 1
            if ticket.stage_id.name == 'Resolved':
                month = ticket.write_date.strftime('%B')
                if month in last_6_months:
                    monthly_resolved[month] += 1
        
        return {
            'status': {
                'labels': list(status_count.keys()),
                'data': list(status_count.values())
            },
            'priority': {
                'labels': list(priority_count.keys()),
                'data': list(priority_count.values())
            },
            'monthly': {
                'labels': last_6_months,
                'new': [monthly_new[month] for month in last_6_months],
                'resolved': [monthly_resolved[month] for month in last_6_months]
            },
            'total_tickets': len(tickets),
            'open_tickets': sum(1 for t in tickets if t.stage_id.name != 'Closed'),
            'resolved_tickets': sum(1 for t in tickets if t.stage_id.name == 'Resolved'),
            'avg_response_time': '24h'  # This should be calculated based on your business logic
        }

    def _get_ticket_sla_data(self, ticket):
        """Calculate SLA performance data for a ticket."""
        # Get SLA policies for the ticket
        sla_policies = request.env['helpdesk.sla'].sudo().search([
            ('team_id', '=', ticket.team_id.id),
            ('priority', '=', ticket.priority),
        ])

        response_time = None
        resolution_time = None
        
        # Calculate response time (time to first response)
        if ticket.message_ids:
            first_response = ticket.message_ids.filtered(lambda m: m.message_type == 'comment' and m.author_id.id != ticket.partner_id.id)
            if first_response:
                response_time = (first_response[0].create_date - ticket.create_date).total_seconds() / 3600  # in hours

        # Calculate resolution time
        if ticket.stage_id.is_closed:
            resolution_time = (ticket.write_date - ticket.create_date).total_seconds() / 3600  # in hours

        # Prepare SLA data for charts
        sla_data = {
            'response': {
                'labels': ['Response Time'],
                'datasets': [{
                    'label': 'Hours',
                    'data': [response_time if response_time else 0],
                    'backgroundColor': ['#36A2EB'],
                    'borderColor': ['#2e86c1'],
                    'borderWidth': 1
                }]
            },
            'resolution': {
                'labels': ['Resolution Time'],
                'datasets': [{
                    'label': 'Hours',
                    'data': [resolution_time if resolution_time else 0],
                    'backgroundColor': ['#4BC0C0'],
                    'borderColor': ['#2e8b57'],
                    'borderWidth': 1
                }]
            }
        }

        return sla_data

    @http.route(['/helpdesk/portal'], type='http', auth="user", website=True)
    def helpdesk_portal(self, **kw):
        user = request.env.user
        company = request.env.company

        # Get user's tickets
        domain = [('create_uid', '=', user.id)]
        tickets = request.env['helpdesk.ticket'].search(domain, order='create_date desc')

        # Calculate statistics
        total_tickets = len(tickets)
        open_tickets = len(tickets.filtered(lambda t: not t.stage_id.is_closed))
        resolved_tickets = len(tickets.filtered(lambda t: t.stage_id.is_closed))

        # Calculate average response time
        avg_response = "N/A"
        response_times = []
        for ticket in tickets:
            response_data = self._get_ticket_sla_data(ticket)
            if response_data.get('response', {}).get('datasets', [{}])[0].get('data', [0])[0]:
                response_times.append(response_data['response']['datasets'][0]['data'][0])
        
        if response_times:
            avg_hours = sum(response_times) / len(response_times)
            if avg_hours < 24:
                avg_response = f"{avg_hours:.1f}h"
            else:
                avg_response = f"{(avg_hours/24):.1f}d"

        # Prepare ticket data for template
        ticket_data = []
        for ticket in tickets:
            ticket_data.append({
                'id': ticket.id,
                'name': ticket.name,
                'description': ticket.description or '',
                'stage_id': ticket.stage_id,
                'priority': ticket.priority or '0',
                'create_date': ticket.create_date,
                'write_date': ticket.write_date,
            })

        # Prepare chart data
        status_data = {
            'labels': [],
            'data': []
        }
        stage_counts = {}
        for ticket in tickets:
            stage_name = ticket.stage_id.name
            stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1

        for stage, count in stage_counts.items():
            status_data['labels'].append(stage)
            status_data['data'].append(count)

        monthly_data = {
            'labels': [],
            'new': [],
            'resolved': []
        }

        # Get data for the last 6 months
        end_date = Date.today()
        start_date = end_date - relativedelta(months=6)
        months = []
        current = start_date
        while current <= end_date:
            months.append(current)
            current += relativedelta(months=1)

        for month in months:
            month_start = month.replace(day=1)
            month_end = month + relativedelta(months=1, days=-1)
            
            monthly_data['labels'].append(month.strftime('%B'))
            monthly_data['new'].append(len(tickets.filtered(
                lambda t: month_start <= t.create_date.date() <= month_end
            )))
            monthly_data['resolved'].append(len(tickets.filtered(
                lambda t: t.stage_id.is_closed and month_start <= t.write_date.date() <= month_end
            )))

        # Load and render template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'portal_dashboard.html')
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))

        html_content = template.render(
            user=user,
            company=company,
            tickets=ticket_data,
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            avg_response=avg_response,
            statusChartData=json.dumps({
                'type': 'doughnut',
                'data': {
                    'labels': status_data['labels'],
                    'datasets': [{
                        'data': status_data['data'],
                        'backgroundColor': ['#3498db', '#f1c40f', '#2ecc71', '#95a5a6'],
                        'borderWidth': 1
                    }]
                }
            }),
            monthlyChartData=json.dumps({
                'type': 'line',
                'data': {
                    'labels': monthly_data['labels'],
                    'datasets': [
                        {
                            'label': 'New Tickets',
                            'data': monthly_data['new'],
                            'borderColor': '#3498db',
                            'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                            'tension': 0.4,
                            'fill': True
                        },
                        {
                            'label': 'Resolved Tickets',
                            'data': monthly_data['resolved'],
                            'borderColor': '#2ecc71',
                            'backgroundColor': 'rgba(46, 204, 113, 0.1)',
                            'tension': 0.4,
                            'fill': True
                        }
                    ]
                }
            })
        )

        return Response(html_content, content_type='text/html')

    @http.route(['/helpdesk/ticket/<int:ticket_id>'], type='http', auth='user', website=True)
    def ticket_detail(self, ticket_id, **kw):
        # Get the ticket
        ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
        
        # Security check
        if ticket.create_uid != request.env.user:
            return request.redirect('/helpdesk/portal')
            
        # Get ticket messages and attachments
        messages = []
        for message in ticket.message_ids:
            attachments = []
            for attachment in message.attachment_ids:
                attachments.append({
                    'name': attachment.name,
                    'size': format_file_size(attachment.file_size),
                    'url': f'/web/content/{attachment.id}?download=true'
                })
                
            messages.append({
                'id': message.id,
                'body': message.body or '',
                'author': message.author_id.name,
                'date': message.create_date,
                'attachments': attachments
            })

        # Get SLA data
        sla_data = self._get_ticket_sla_data(ticket)
            
        # Load and render template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'ticket_detail.html')
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))
        
        html_content = template.render(
            user=request.env.user,
            company=request.env.company,
            ticket={
                'id': ticket.id,
                'name': ticket.name,
                'description': ticket.description or '',
                'stage_id': ticket.stage_id,
                'priority': ticket.priority or '0',
                'create_date': ticket.create_date,
                'write_date': ticket.write_date,
                'messages': messages
            },
            sla_data=json.dumps(sla_data)
        )
        
        return Response(html_content, content_type='text/html')

    @http.route(['/helpdesk/ticket/<int:ticket_id>'], type='http', auth='user', website=True)
    def ticket_details(self, ticket_id, **kw):
        # Get ticket
        ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
        
        # Security check
        if ticket.partner_id != request.env.user.partner_id:
            return request.not_found()
            
        # Convert ticket data
        priority_map = {
            '0': {'text': 'Low Priority', 'class': 'priority-low'},
            '1': {'text': 'Medium Priority', 'class': 'priority-medium'},
            '2': {'text': 'High Priority', 'class': 'priority-high'}
        }
        
        status_class_map = {
            'new': 'status-new',
            'in_progress': 'status-in-progress',
            'resolved': 'status-resolved',
            'closed': 'status-closed'
        }
        
        ticket_data = {
            'id': ticket.id,
            'number': f"#{ticket.id}",
            'title': ticket.name,
            'description': ticket.description or '',
            'status': ticket.stage_id.name,
            'status_class': status_class_map.get(ticket.stage_id.name.lower().replace(' ', '_'), 'status-new'),
            'created_date': ticket.create_date.strftime('%b %d, %Y'),
            'priority': priority_map.get(str(ticket.priority), priority_map['0']),
            'last_update': ticket.write_date,
        }
        
        # Get SLA performance data
        sla_data = self._get_ticket_sla_data(ticket)
        
        # Set up Jinja environment
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('ticket_details.html')
        
        # Render template
        html_content = template.render(
            ticket=ticket_data,
            company=request.env.company,
            sla_data=json.dumps(sla_data)
        )
        
        return Response(html_content, content_type='text/html')
