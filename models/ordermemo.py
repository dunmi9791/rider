# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'subject'
    _description = 'Order Memo'

    subject = fields.Char(string="Subject")
    employee_from_id = fields.Many2one(comodel_name="res.users", string="From", required=False, )
    employee_to_id = fields.Many2one(comodel_name="res.users", string="To", required=False, )
    date = fields.Date(string="Date", required=False, )
    memo_content = fields.HTML(string="",  )


