{
    'name': 'Extended Aged Partner Reports',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Reports',
    'summary': 'Add payment terms column to aged receivable and payable reports',
    'description': """
        This module extends the aged receivable and payable reports by adding payment terms columns.
        - Adds payment terms to aged receivable report
        - Adds payment terms to aged payable report
    """,
    'depends': ['account_reports'],
    'data': [
        'views/aged_partner_reports.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
