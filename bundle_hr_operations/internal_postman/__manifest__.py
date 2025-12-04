{
    'name': 'Internal Postman Courier Management messaging',
    'version': '17.0',
    'category': 'Internal',
    'license': 'LGPL-3',
    'description': """
     This Module will manage incoming couriers and packages.
     It will add a flow to collect -> Assign -> Received for covers and parcels
     received.
     """,
    'summary': """
     This Module will manage incoming couriers and packages.
     It will add a flow to collect -> Assign -> Received for covers and parcels
     received.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'https://www.serpentcs.com',
    'depends': [
        'base',
        'mail',
        'hr',
        'project',
        ],
    'data': [
        'security/ir.model.access.csv',
        'data/courier_sequence.xml',
        'views/internal_postman_view.xml',
        'views/courier_inwd_outwd_list_report_view.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': [
        'static/description/IP-banner.png'],
    'price': 10,
    'currency': 'EUR'
}