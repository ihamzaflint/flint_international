{
    'name': 'SAIB Bank Integration',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Integration with SAIB Bank B2B APIs',
    'description': """
        This module provides integration with SAIB Bank B2B APIs including:
        * Bulk Payments
        * Single Payments
        * Payroll Processing
        * Bank Statements
        * Account Balance Enquiry
        
        Features:
        - JWS signature support for API requests
        - Configurable API endpoints and credentials
        - Support for both single and bulk payments
        - Comprehensive error handling and logging
        - Support for both Saudi and Riyad Bank
    """,
    'author': 'Flint Tech Team - Omar K. Ali',
    'depends': ['base', 'account', 'hr_payroll', 'l10n_sa_hr_payroll', 'hr_allowance_deduction'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/saib_payment_views.xml',
        'views/saib_payroll_views.xml',
        'views/saib_bank_statement_views.xml',
        'views/res_company_views.xml',
        'views/hr_payslip_run_views.xml',
        'views/res_partner_bank_views.xml',
        
    ],
    'external_dependencies': {
        'python': ['cryptography'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
