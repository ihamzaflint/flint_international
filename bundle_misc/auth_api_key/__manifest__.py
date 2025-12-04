# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'API Key Authentication',
    'version': '17.0.1.0.0',
    'category': 'Hidden/Tools',
    'summary': 'API Key Authentication for Mobile Apps',
    'description': """
        This module provides API Key authentication mechanism for mobile applications.
        Features:
        - Token-based authentication
        - Token expiry management
        - API key validation
    """,
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
