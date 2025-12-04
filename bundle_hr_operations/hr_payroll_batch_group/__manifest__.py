{
    'name': 'HR Payroll Batch Group',
    'summary': """
     Adds security group on payroll batch Create Draft Entry button
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'version': '1.0',
    'depends': [
        'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_payroll_run_views.xml'],
    'installable': True
}