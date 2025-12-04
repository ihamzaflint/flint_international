{
    'name': 'IBAN Change Request ',
'version' : '1.2',
    'summary': '',
    'description': '',
    'category': 'Base',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'contacts','helpdesk'
        ],
    'data': [
        "security/ir.model.access.csv",
        "data/data.xml",
        "data/mail_template.xml",
        'views/iban_change_request.xml',
        'wizards/reject_reason.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
'license': 'LGPL-3',
}