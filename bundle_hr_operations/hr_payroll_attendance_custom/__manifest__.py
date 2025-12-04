{
    'name': 'HR Payroll linked with Attendance',
    'summary': """
     
     """,
    'description': """
     Long description of module's purpose
     """,
    'author': 'Aasim Ahmed Ansari',
    'website': 'http://aasimania.wordpress.com',
    'category': 'Human Resources',
    'version': '17.0.1.0.1',
    'depends': [
        'hr_attendance',
        'hr_payroll',
        'account',
        'hr_holidays',
        'hr_generate_payslip_filter'],
    'data': [
        'data/hr_work_entry_type.xml',
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'wizard/hr_attendance_update_view.xml',
        'wizard/refresh_payslip_view.xml',
        'views/views.xml',
        'views/hr_payroll_views.xml',
        'views/res_config_view.xml',
        'views/hr_contract_views.xml',
        'views/hr_attendance_summary_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_attendance_adjustment_view.xml',
        'views/hr_attendance_summary_report_template.xml',
        'views/reports.xml',
        'views/resource_views.xml',
        'wizard/hr_attendance_summary_import.xml',
        'views/hr_attendance_policy.xml',
        'views/hr_work_entry_type.xml'],
    'license': 'LGPL-3',
    'installable': True
}