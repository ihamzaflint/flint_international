{
    'name': 'SAIB Bank Government Payment Integration',
    'version': '1.0',
    'category': 'Accounting/Payment',
    'summary': 'Integration with SAIB Bank for Government Payments',
    'description': """
        This module provides integration with SAIB Bank for processing government payments.
        Features:
        - Create and manage SAIB bank payment records
        - Process single and batch payments
        - Track payment status and bank references
    """,
    'depends': [
        'base',
        'account',
        'scs_operation',
        'saib_bank_integration',
    ],
    'data': [
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}