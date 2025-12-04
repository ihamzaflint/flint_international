{
    'name': 'Purchase Dynamic Approval',
    'summary': 'Allow to request approval based on approval matrix',
    'author': 'Abdalla Mohamed & Omar Khaled',
    'maintainer': 'Abdalla Mohamed & Omar Khaled',
    'version': '17.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'base_dynamic_approval',
        'purchase',
        'base_dynamic_approval_role'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/confirm_purchase_order_wizard.xml',
        'views/purchase_order.xml',
        'views/purchase_order_history_view.xml',
        'data/mail_template.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}