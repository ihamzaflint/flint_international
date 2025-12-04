{
    'name': 'Purchase Order Qweb',
    'summary': """
     Purchase order qweb reports.
     """,
    'description': """
     Purchase order qweb report.
     """,
    'author': 'Palmate',
    'website': 'http://www.palmate.in',
    'category': 'Purchase',
    'version': '0.1',
    'depends': [
        'purchase',
        'purchase_approved_user'],
    'data': [
        'report/report_purchase.xml',
        'views/purchase_report_view.xml'],
    'demo': [
        'demo/demo.xml'],
    'license': 'LGPL-3',
    'installable': True
}