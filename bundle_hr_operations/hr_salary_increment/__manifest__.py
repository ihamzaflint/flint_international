{
    'name': 'HR Salary Increment',
    'summary': 'Salary increment',
    'version': '1.0',
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'category': 'Payroll',
    'depends': [
        'hr',
        'hr_payroll',
        'mail',
        'hr_work_entry_contract_enterprise',
        'hr_generate_payslip_filter',
        'hr_payroll_attendance_custom'],
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_salary_increment_views.xml',
        'views/hr_salary_parameter_views.xml',
        'views/hr_salary_rule_views.xml'],
    'demo': [],
    'license': 'AGPL-3',
    'installable': True
}