{
    'name': 'Flint Helpdesk Portal',
    'version': '1.0',
    'category': 'Services/Helpdesk',
    'sequence': 1,
    'summary': 'Helpdesk Portal for Flint',
    'description': """
        Helpdesk Portal for Flint
    """,
    'depends': [
        'portal',
        'helpdesk',
        'web',
        'flint_helpdesk',
    ],
    'data': [
        'security/ir.model.access.csv',
        'templates/portal_dashboard.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Chart.js library
            ('include', 'https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js'),
            # Custom assets
            '/flint_helpdesk_portal/static/css/portal_dashboard.css',
            '/flint_helpdesk_portal/static/js/portal_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
