# -*- coding: utf-8 -*-
{
    'name': "ITQ Alert Wizard",

    'summary': """
    """,

    'description': """
    """,

    'author': "Itqan Systems",

    'website': "http://www.itqansystems.com",

    'category': 'Utilities',

    'version': '14.0',


    # any module necessary for this one to work correctly
    'depends': [
        'base',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/alert_wizard_views.xml',
    ],
    
    'application': False,
}