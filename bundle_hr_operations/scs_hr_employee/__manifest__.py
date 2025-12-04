{
    'name': 'Employee Code',
    'version': '1.1',
    'summary': '',
    'description': '',
    'category': 'Base',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'hr_employee_code',
        'hr_employee_profession',
        'account',
        'scs_hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/client_type_view.xml',
        'views/client_client_view.xml',
        'views/client_project_view.xml',
        'views/employee_degree_view.xml',
        'views/hr_employee_view.xml',
        'views/account_view.xml',
        'views/res_partner_bank_view.xml',
        'wizard/import_employee_details.xml'],
    'installable': True,
    'application': False
}
