{
    'name': 'Salary Rule Global',
    'summary': """
     
     """,
    'description': """
     Allows creation of global rules which will be independent of any structure. These rules will be applicable to any
     payslip which has respective transactions validated.
     """,
    'author': 'Palmate Technologies',
    'website': 'http://www.yourcompany.com',
    'category': 'Human Resources/Payroll',
    'version': '17.0',
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll_account',
        'account'],
    'data': [
        'views/hr_salary_views.xml',
        'views/templates.xml',
        'views/hr_payslip_view.xml'],
    'installable': True
}