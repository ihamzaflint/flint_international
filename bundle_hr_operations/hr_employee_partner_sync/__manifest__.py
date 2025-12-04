{
    'name': 'HR Employee Partner Sync',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Sync HR Employees with Partners',
    'description': """
        Link HR Employee records with Partner records based on matching names.
        Updates address_id and work_contact_id fields.
    """,
    'depends': ['hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
