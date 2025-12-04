{
    'name': 'Account Moves Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Omar Abdeif',
    'maintainer': 'Omar Abdeif',
    'version': '17.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval',
        'account_accountant',
        'base_dynamic_approval_role',
        'account_edi'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_account_move_wizard.xml',
        'views/account_move.xml',
        'views/account_move_history_view.xml',
        'data/mail_template.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}