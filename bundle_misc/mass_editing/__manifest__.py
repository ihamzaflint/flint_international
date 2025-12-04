{
    'name': 'Mass Editing',
    'version': '1.0',
    'author': 'Serpent Consulting Services Pvt. Ltd., Tecnativa, GRAP, Iván Todorovich, Odoo Community Association (OCA)',
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-ux',
    'license': 'AGPL-3',
    'summary': 'Mass Editing',
    'depends': [
        'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_actions_server.xml',
        'wizard/mass_editing_wizard.xml'],
    'demo': [
        'demo/mass_editing.xml'],
    'installable': True
}