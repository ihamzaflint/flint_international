{
    'name': 'Mobile API',
    'version': '1.0',
    'category': 'Technical',
    'summary': 'RESTful API for Mobile Applications',
    'description': """
        This module provides RESTful API endpoints to power mobile applications.
        Features include:
        - User authentication
        - Helpdesk ticket management
        - Real-time updates and notifications
        - Offline support
    """,
    'author': 'Odoo',
    'website': 'https://www.odoo.com',
    'depends': [
        'base',
        'web',
        'helpdesk',
        'auth_signup',
        'mail',
    ],
    'data': [
        'security/mobile_api_security.xml',
        'security/ir.model.access.csv',
        'views/mobile_user_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['pyjwt', 'cryptography'],
    },
}
