# -*- coding: utf-8 -*-
# from odoo import http


# class SaleCancelGroup(http.Controller):
#     @http.route('/sale_cancel_group/sale_cancel_group/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_cancel_group/sale_cancel_group/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_cancel_group.listing', {
#             'root': '/sale_cancel_group/sale_cancel_group',
#             'objects': http.request.env['sale_cancel_group.sale_cancel_group'].search([]),
#         })

#     @http.route('/sale_cancel_group/sale_cancel_group/objects/<model("sale_cancel_group.sale_cancel_group"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_cancel_group.object', {
#             'object': obj
#         })
