{
    'name': 'HR Payroll Approver',
    'summary': """
     HR Payroll batch approver process
     """,
    'description': """
     HR Payroll batch approver process
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.sa',
    'category': 'HR/Payroll',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': [
        'hr_payroll',
        'hr_payroll_account'
    ],
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/hr_payslip_run.xml',
        'views/hr_payslip_run_views.xml',
        'wizards/payroll_rejection_reason_wizard_views.xml'],
    'installable': True
}