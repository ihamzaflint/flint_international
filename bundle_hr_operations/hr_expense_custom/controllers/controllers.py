# -*- coding: utf-8 -*-
# from odoo import http


# class HrExpenseCustom(http.Controller):
#     @http.route('/hr_expense_custom/hr_expense_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_expense_custom/hr_expense_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_expense_custom.listing', {
#             'root': '/hr_expense_custom/hr_expense_custom',
#             'objects': http.request.env['hr_expense_custom.hr_expense_custom'].search([]),
#         })

#     @http.route('/hr_expense_custom/hr_expense_custom/objects/<model("hr_expense_custom.hr_expense_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_expense_custom.object', {
#             'object': obj
#         })
