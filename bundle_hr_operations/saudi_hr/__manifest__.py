{
    'name': 'HR Saudi',
    'version': '1.1',
    'summary': '',
    'description': '',
    'category': 'Base',
    'author': 'Palmate',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'hr_contract',
        'analytic',
        'hr_payroll_account',
        'hijri_date_util'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/hr_sponsor.xml',
        'views/hr_contract.xml'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False
}