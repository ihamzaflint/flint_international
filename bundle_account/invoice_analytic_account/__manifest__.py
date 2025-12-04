{
    'name': 'Invoice Analytic Account',
    'summary': """
     -Added Analytic account field in Invoice.
     """,
    'description': """
     -Added Analytic account field in Invoice.
     """,
    'author': 'Palmate',
    'website': 'http://www.yourcompany.com',
    'category': 'Accounting',
    'version': '0.1',
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'analytic'],
    'data': [
        'views/account_move_view.xml'],
    'demo': [
        'demo/demo.xml'],
    'license': 'LGPL-3',
    'installable': True
}