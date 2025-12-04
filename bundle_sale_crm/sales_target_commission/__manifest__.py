{
    'name': 'sales_target_commission',
    'version': '17.1',
    'summary': 'Sales team target and compute  commission',
    'category': 'Sales',
    'author': 'Itqan Systems',
    'website': 'http://www.itqansystems.com',
    'license': 'AGPL-3',
    'depends': [
        'sale_management',
        ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence.xml',
        'data/sales_team_target_cron.xml',
        'views/commission_policy_view.xml',
        'views/sales_team_target_view.xml',
        'views/sales_commission_lines_view.xml',
        'reports/sales_team_target_report.xml']
}