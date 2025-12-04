{
    'name': 'HR Expense Extend',
    'version': '17.0.0.0.1',
    'summary': 'HR Expense Extend',
    'description': 'To provide approval hierarchy for expense module and show the petty cash balance, designed specifically based on Flint International SOP.',
    'category': 'HR',
    'author': 'Muhammad Hamza Faizan',
    'website': "linkedin.com/in/muhammad-hamza-faizan",
    'license': 'LGPL-3',
    'depends': [
        'hr_expense',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_sheet.xml',
        'views/expense_approval_config.xml',
        'views/account_journal.xml',
        'views/account_payment_register.xml',
        'views/menuitems.xml'
    ],
    'installable': True,
    'auto_install': False,
}