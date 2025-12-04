{
    'name': 'HR Employee Document Generator',
    'summary': """
     Generates the employee documents like Job Offer, Attested docs etc
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'license': 'AGPL-3',
    'category': 'Base',
    'version': '1.0',
    'depends': [
        'hr',
        'hr_contract'],
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'wizard/hr_employee_doc_wizard_view.xml',
        'report/report.xml',
        'report/report_embassy-male.xml'],
    'installable': True,
    'application': True
}