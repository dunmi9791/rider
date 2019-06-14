# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _inherit = ['mail.thread']
    _rec_name = 'subject'
    _description = 'Order Memo'

    subject = fields.Char(string="Subject")

    date = fields.Date(string="Date", required=False, )
    memo_content = fields.Html(string="",  )
    memo_to = fields.Many2one(comodel_name="hr.employee", string="To", )
    state = fields.Selection(string="", selection=[('new', 'new'), ('approved', 'approved'), ('canceled', 'canceled') ], required=False, default='new', track_visibility='onchange' )
