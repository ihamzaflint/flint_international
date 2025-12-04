{
    'name': 'HR Payslip Send Mail',
    'summary': """
     Send payslip by email to employees.
     """,
    'description': """
     Send payslip by email to employees.
     """,
    'author': 'Palmate',
    'website': 'https://www.palmate.in',
    'category': 'Human Resources/Payslip',
    'version': '17.0',
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll_account',
        'hr_payroll',
        'saudi_hr',
        'hr_generate_payslip_filter'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/hr_payslip_views.xml',
        'wizard/send_mail_from_date_view.xml',
        'wizard/generate_batch_payslip_view.xml'],
    'installable': True
}