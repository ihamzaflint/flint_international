# -*- coding: utf-8 -*-
{
    'name': 'Requisition Form',
    'version': '1.0',
    'summary': 'Requisition Form',
    'description': """
        Requisition Form
    """,
    'category': 'Purchase',
    'author': 'Naveed Ajmal | Hashverx',
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/vendor_default_select.xml',
        'views/requisition_form.xml',
        'views/purchase_approval_config.xml',
        'views/purchase_order.xml',
        'views/menuitem.xml',
    ],

    'installable': True,
    'application': True,
}
