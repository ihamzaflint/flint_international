# -*- coding: utf-8 -*-
{
    'name': 'Asset Handover Report',
    'version': '1.0',
    'summary': 'Asset Handover Report',
    'description': """
        Contract Between the Company and Employee To Use Company Device Sincerely
    """,
    'category': 'HR',
    'author': 'Muhammad Hamza Faizan',
    'website': 'https://www.linkedin.com/in/muhammad-hamza-faizan/',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/asset_handover_report_action.xml',
        'report/asset_handover_report_template.xml',
        'views/asset_handover_report_info.xml',
        'views/menuitem.xml',
    ],
    'icon': '/asset_handover_report/static/src/img/icon.png',
}
