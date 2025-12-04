{
    'name': 'Base Tier Validation',
    'summary': 'Implement a validation process based on tiers.',
    'version': '1.3',
    'development_status': 'Mature',
    'maintainers': [
        'LoisRForgeFlow'],
    'category': 'Tools',
    'website': 'https://github.com/OCA/server-ux',
    'author': 'ForgeFlow, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'mail'],
    'data': [
        'data/mail_data.xml',
        'security/ir.model.access.csv',
        'security/tier_validation_security.xml',
        'views/res_config_settings_views.xml',
        'views/tier_definition_view.xml',
        'views/tier_review_view.xml',
        'wizard/comment_wizard_view.xml',
        'templates/tier_validation_templates.xml'],
    'assets': {'web.assets_backend': [], 'web.assets_qweb': []}
}