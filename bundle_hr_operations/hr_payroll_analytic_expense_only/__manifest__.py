{
    'name': 'HR Payroll Analytic Expense Only',
    'summary': """
     
     """,
    'description': """
     The journal entry of a payslip will select analytic account only if the corresponding general account is not of receivable or payable nature.
     """,
    'author': 'Aasim Ahmed Ansari',
    'website': 'http://www.yourcompany.com',
    'category': 'Human Resources/Payroll',
    'version': '17.0',
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll_account'],
    'data': [
        'views/views.xml',
        'views/templates.xml'],
    'installable': True
}