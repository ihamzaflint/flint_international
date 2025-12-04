{
    'name': 'HR Payslip Batch Export',
    'summary': """
     This module Export the payslips data in xls format
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'license': 'AGPL-3',
    'category': 'Payroll',
    'version': '1.0',
    'depends': [
        'hr_payroll',
        'report_xlsx',
        'saib_bank_integration',
        'l10n_sa_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'report/report.xml',
        'wizard/wizard_export_batch_view.xml'],
    'installable': True
}