{
    'name': 'Hijri Date Util',
    'version': '17.1',
    'summary': 'Um Alqura Hijri date widget',
    'description': 'this module would enable hijri date widget across Odoo platform',
    'author': 'Omar Abdeif',
    'category': 'Hidden/Tools',
    'depends': [
        'account',
        'base',
        'web'],
    'data': [],
    'demo': [
        ''],
    'auto_install': False,
    'application': False,
    'installable': True,
    'assets': {'web.assets_common': ['hijri_date_util/static/lib/tempusdominus6/tempusdominus.css', 'hijri_date_util/static/lib/popper/popper.js', 'hijri_date_util/static/lib/tempusdominus6/tempusdominus.js'], 'web.assets_backend': ['hijri_date_util/static/src/datepicker_hijri/datepicker_hijri.js', 'hijri_date_util/static/src/datepicker_hijri/datepicker_hijri.xml', 'hijri_date_util/static/src/fields/date_field_hijri.js', 'hijri_date_util/static/src/fields/date_field_hijri.xml', 'hijri_date_util/static/src/fields/datetime_field_hijri.js', 'hijri_date_util/static/src/fields/datetime_field_hijri.xml']},
    'qweb': [],
    'images': [
        'static/description/icon.svg'],
    'license': 'OPL-1'
}