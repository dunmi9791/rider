# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="Memo Subject", required=False,)

    date = fields.Date(string="", required=False, )
    memo = fields.Html(string="",  )
    order_id = fields.Many2one(comodel_name="order.rider", string="order", required=False, )
    memo_to = fields.Many2one(comodel_name="hr.employee", string="Memo to", )
