{
    'name': 'Expense Qweb Report',
    'summary': """
     Add Analytic Account/Project in Expense Report.
     """,
    'description': """
     Add Analytic Account/Project in Expense Report.
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'license': 'AGPL-3',
    'category': 'Base',
    'version': '1.0',
    'depends': [
        'hr',
        'hr_expense'],
    'data': [
        'report/report_expense_inherit.xml'],
    'installable': True
}