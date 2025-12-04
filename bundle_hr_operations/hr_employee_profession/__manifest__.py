{
    'name': 'Hr Employee Profession',
    'summary': """
     Adds employee profession master
     """,
    'description': """
     Adds employee profession master
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'category': '',
    'version': '0.1',
    'depends': [
        'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_profession_views.xml',
        'views/hr_employee_views.xml'],
    'demo': [
        'demo/demo.xml'],
    'license': 'LGPL-3',
    'installable': True
}