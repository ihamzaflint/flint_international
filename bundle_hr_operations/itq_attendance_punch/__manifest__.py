{
    'name': 'Attendance Punch',
    'summary': """
     Get transaction from ZK Teco finger print system
     """,
    'author': 'Omar Khaled Ali',
    'maintainer': 'Omar Khaled Ali',
    'website': 'https://www.linkedin.com/in/omar-khaled-4a706b11b/',
    'category': 'Human Resource',
    'version': '17.0',
    'license': 'AGPL-3',
    'depends': [
        'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/sequence.xml',
        'data/itq_punch_machine.xml',
        'views/punch_import_action.xml',
        'views/res_config_settings.xml',
        'views/zk_transaction_views.xml',
        'views/hr_employee_views.xml',
        'views/punch_import_history_views.xml',
        'views/itq_attendance_fp_config_view.xml']
}