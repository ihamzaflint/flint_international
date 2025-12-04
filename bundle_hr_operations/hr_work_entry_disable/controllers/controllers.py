# -*- coding: utf-8 -*-
# from odoo import http


# class HrWorkEntryDisable(http.Controller):
#     @http.route('/hr_work_entry_disable/hr_work_entry_disable', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_work_entry_disable/hr_work_entry_disable/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_work_entry_disable.listing', {
#             'root': '/hr_work_entry_disable/hr_work_entry_disable',
#             'objects': http.request.env['hr_work_entry_disable.hr_work_entry_disable'].search([]),
#         })

#     @http.route('/hr_work_entry_disable/hr_work_entry_disable/objects/<model("hr_work_entry_disable.hr_work_entry_disable"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_work_entry_disable.object', {
#             'object': obj
#         })
