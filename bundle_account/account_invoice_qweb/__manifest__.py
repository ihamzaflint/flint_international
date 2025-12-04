{
    'name': 'Account Invoice Qweb',
    'summary': """
     Invoice Qweb Reports
     """,
    'description': """
     Invoice Qweb Reports
     """,
    'author': 'Palmate',
    'website': 'http://www.yourcompany.com',
    'category': 'Accounting',
    'version': '17.0.1.0.3',
    'depends': [
        'base',
        'account',
        'account_accountant',
        'web',
        'invoice_analytic_account',
        'invoice_line_quantity_str',
        'product',
        'l10n_gcc_invoice',
        'contacts_extend',
    ],
    'data': [
        'views/report_invoice.xml',
        'views/report_invoice_stc.xml',
        'views/report_invoice_ericson.xml',
        'views/account_report.xml',
        'views/account_move_view.xml',
        'views/report_journal.xml',
        'views/product_views.xml',
        'views/res_partner_view.xml',
        "views/res_company.xml",
        "views/account_reconcile_lines.xml"],
    'assets': {'web.assets_qweb': ['account_invoice_qweb/static/src/xml/account_reconciliation.xml']},
    'demo': [
        'demo/demo.xml'],
    'license': 'LGPL-3',
    'installable': True
}