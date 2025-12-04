{
    'name': 'Account Analytic Parent',
    'summary': """
     This module reintroduces the hierarchy to the analytic accounts.
     """,
    'version': '1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'author': 'Matmoz d.o.o., Luxim d.o.o., Deneroteam, ForgeFlow, Tecnativa, CorporateHub, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-analytic',
    'depends': [
        'account',
        'analytic'],
    'data': [
        'views/account_analytic_account_view.xml'],
    'demo': [
        'demo/analytic_account_demo.xml'],
    'post_init_hook': 'post_init_hook',
    'installable': True
}