{
    'name': 'HR Allowance Deduction',
    'version': '1.0',
    'summary': ' Allows to add adjustments in payslip ex Loan deduction, Traffic violation penalty etc ',
    'description': ' Allows to add adjustments in payslip ex Loan deduction, Traffic violation penalty etc ',
    'category': 'Human Resources/Payroll',
    'author': 'Palmate',
    'website': '',
    'license': 'AGPL-3',
    'depends': [
        'hr_payroll',
        'hr_work_entry_contract_enterprise',
        'l10n_sa_hr_payroll',
        'hr_payroll_attendance_custom',
        'saudi_hr',
        'hr_salary_rule_global'],
    'data': [
        'security/ir.model.access.csv',
        'views/other_hr_payslip.xml',
        'views/hr_payslip_view.xml',
        'wizard/mass_approve_adjustment.xml'],
    'demo': [],
    'installable': True,
    'application': False
}