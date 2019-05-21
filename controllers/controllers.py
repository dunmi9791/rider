# -*- coding: utf-8 -*-
from odoo import http

# class Rider(http.Controller):
#     @http.route('/rider/rider/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rider/rider/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rider.listing', {
#             'root': '/rider/rider',
#             'objects': http.request.env['rider.rider'].search([]),
#         })

#     @http.route('/rider/rider/objects/<model("rider.rider"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rider.object', {
#             'object': obj
#         })