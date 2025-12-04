# -*- coding: utf-8 -*-
{
    'name': 'Loan Management',
    'version': '1.0',
    'summary': 'Loan Management',
    'description': """
        Loan Management
    """,
    'category': 'HR',
    'author': 'Muhammad Hamza Faizan',
    'website': 'https://www.linkedin.com/in/muhammad-hamza-faizan/',
    'depends': ['base', 'mail', 'hr', 'flint_helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan.xml',
        'views/request_hr_loan.xml',
        'views/loan_approval_config.xml',
        'views/menuitem.xml',
    ],
    'icon': '/loan_management/static/src/img/icon.png',
}