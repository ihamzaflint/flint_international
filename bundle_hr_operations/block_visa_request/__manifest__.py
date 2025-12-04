# -*- coding: utf-8 -*-
{
    'name': 'Block Visa Request Management',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage block visa requests for expatriate employees',
    'description': """
Block Visa Request Management
============================
This module helps manage the process of requesting and tracking block visas for expatriate employees in Saudi Arabia.

Features:
---------
* Create and manage block visa requests
* Track company and project information
* Monitor Saudization compliance
* Manage job categories and requirements
* Document management system
* Workflow approval process
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'hr',
        'documents'
    ],
    'data': [
        'security/block_visa_security.xml',
        'security/ir.model.access.csv',
        'views/block_visa_views.xml',
        'data/ir_sequence_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'license': 'LGPL-3',
}