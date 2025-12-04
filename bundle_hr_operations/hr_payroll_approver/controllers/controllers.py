# -*- coding: utf-8 -*-
# from odoo import http


# class HrPayrollApprover(http.Controller):
#     @http.route('/hr_payroll_approver/hr_payroll_approver', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_payroll_approver/hr_payroll_approver/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_payroll_approver.listing', {
#             'root': '/hr_payroll_approver/hr_payroll_approver',
#             'objects': http.request.env['hr_payroll_approver.hr_payroll_approver'].search([]),
#         })

#     @http.route('/hr_payroll_approver/hr_payroll_approver/objects/<model("hr_payroll_approver.hr_payroll_approver"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_payroll_approver.object', {
#             'object': obj
#         })
