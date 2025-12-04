{
    'name': 'Account Move Extend',
    'summary': """
     Account Move Extend
     """,
    'description': """
     Account Move Extend
     """,
    'author': 'Muhammad Hamza Faizan',
    'website': 'linkedin.com/in/muhammad-hamza-faizan',
    'category': 'Accounting',
    'version': '17.0.0.0.1',
    'depends': [
        'account'
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/account_move.xml",
        "views/res_supply_period.xml",
        "views/menuitem.xml",
    ],
    'license': 'LGPL-3',
    'installable': True
}