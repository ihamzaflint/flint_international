{
    'name': 'Account Reconciliation Model Fix',
    'summary': """
     If tax is selected and then removed in reconciliation window, then the tax grid is not updated.
     This module is written to fix this issue.
     """,
    'description': """
     Long description of module's purpose
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'license': 'AGPL-3',
    'category': 'Accounting/Accounting',
    'version': '0.1',
    'depends': [
        'account_accountant'],
    'data': [
        'views/views.xml',
        'views/templates.xml'],
    'installable': True
}