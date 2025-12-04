{
    'name': 'Hr Payroll Reporting',
    'summary': ' Shows Payroll Detailed Report in Pivot table and export to excel. ',
    'description': ' Shows Payroll Detailed Report in Pivot table and export to excel. ',
    'category': 'HR',
    'version': '1.0',
    'author': 'Palmate',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll',
        'analytic',
        'hr_payroll_account',
        'report_xlsx',
        'scs_hr_employee',
        'hr_payroll_attendance_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/report.xml',
        'views/batch.xml',
        'views/hr_payslip_view.xml',
        'report/payslip_detail_template.xml'],
    'installable': True,
    'auto_install': False,
    'application': False
}