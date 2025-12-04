{
    'name': 'Account Move Print',
    'version': '1.0',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'summary': 'Adds the option to print Journal Entries',
    'author': 'ForgeFlow, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
        'account_reports',
        'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'report/acc_cr_db_report.xml',
        'report/journal_report.xml',
        'wizard/acc_dabit_credit_report_view.xml'],
    'demo': [],
    'installable': True,
    'application': False
}