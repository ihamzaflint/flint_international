# -*- coding: utf-8 -*-
{
    'name': 'Asset Return Report',
    'version': '1.0',
    'summary': 'Asset Return Report',
    'description': """
        Contract Between the Company and Employee To Return Company Device Sincerely
    """,
    'category': 'HR',
    'author': 'Muhammad Hamza Faizan',
    'website': 'https://www.linkedin.com/in/muhammad-hamza-faizan/',
    'depends': ['base', 'mail', 'hr', 'asset_handover_report'],
    'data': [
        'security/ir.model.access.csv',
        'report/asset_return_report_action.xml',
        'report/asset_return_report_template.xml',
        'views/asset_return_report_info.xml',
        'views/menuitem.xml',
    ],
}
