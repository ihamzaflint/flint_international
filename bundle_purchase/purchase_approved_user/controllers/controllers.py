# -*- coding: utf-8 -*-
# from odoo import http


# class PurchaseApprovedUser(http.Controller):
#     @http.route('/purchase_approved_user/purchase_approved_user', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_approved_user/purchase_approved_user/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_approved_user.listing', {
#             'root': '/purchase_approved_user/purchase_approved_user',
#             'objects': http.request.env['purchase_approved_user.purchase_approved_user'].search([]),
#         })

#     @http.route('/purchase_approved_user/purchase_approved_user/objects/<model("purchase_approved_user.purchase_approved_user"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_approved_user.object', {
#             'object': obj
#         })
