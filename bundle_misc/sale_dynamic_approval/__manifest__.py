{
    'name': 'Sales Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Ever Business Solutions',
    'maintainer': 'Abdalla Mohamed',
    'version': '17.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'sale_crm',
        'crm',
        'sale',
        'base_dynamic_approval'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_sale_order_wizard.xml',
        'views/sale_order.xml',
        'data/mail_template.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}