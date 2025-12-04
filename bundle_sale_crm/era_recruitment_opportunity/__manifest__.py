# -*- coding: utf-8 -*-
{
    'name': "era_recruitment_opportunity",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_recruitment', 'crm', 'sale', 'base_automation', 'sale_crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'demo/product_demo.xml',
        'data/applicant_sequence.xml',
        'data/employee_code.xml',
        'data/ir_cron.xml',
        'demo/mail_template_data.xml',
        'report/ir_action_report.xml',
        'report/ir_actions_report_templates.xml',
        'views/job_position_wizard.xml',
        'views/import_job_view.xml',
        'views/import_applicants_view.xml',
        'views/views.xml',
        'views/performance_report.xml',
        'views/recruitment_process_view.xml',
        'views/recruitment_order_view.xml',
        'views/templates.xml',
        'views/portal_template.xml',
        'views/hr_applicant_views.xml',
        'views/sale_order_view.xml',
        'views/product_template_view.xml',
        'views/sale_order_line_view.xml',
        'views/sale_order_service_line_view.xml',
        'views/applicant_reject_reason_template.xml',
        'views/applicant_response_view.xml',
        'views/hr_employee_view.xml',
        'views/recruitment_policy_view.xml',
        'views/res_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'era_recruitment_opportunity/static/src/js/performanceReport.js',
            'era_recruitment_opportunity/static/src/xml/performance_report.xml',
            'era_recruitment_opportunity/static/src/scss/style.css',
        ],
        'web.assets_frontend': [
            'era_recruitment_opportunity/static/src/js/website.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/mail_template_data.xml',

    ],
}
