{
    'name': 'HR Generate Payslips Filter',
    'summary': """
     This module adds different filters in Generate Payslips wizard in Payslip Batches
     """,
    'description': """
     This module adds different filters in Generate Payslips wizard in Payslip Batches
     """,
    'author': 'Aasim Ahmed Ansari',
    'website': 'http://www.yourcompany.com',
    'category': 'Human Resources/Payroll',
    'version': '1.0',
    'depends': [
        'hr_payroll',
        'account_analytic_parent'],
    'data': [
        'wizard/hr_payroll_payslips_by_employees_views.xml',
        'views/hr_payslip_run_view.xml',
        'views/hr_departure_reason_views.xml'],
    'demo': [
        'demo/demo.xml'],
    'license': 'LGPL-3',
    'installable': True
}