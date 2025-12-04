{
    'name': 'Currency Rate Compatibility',
    'version': '1.0',
    'category': 'Hidden',
    'summary': 'Compatibility module for currency rate updates',
    'description': """
Currency Rate Compatibility
===========================

This module adds compatibility for currency rate update functionality when the currency_rate_live module is not installed.
It prevents errors from occurring when the cron job tries to call the run_update_currency method on res.company.
    """,
    'author': 'Flint',
    'website': 'https://www.flint.com',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
