# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'subject'
    _description = 'Order Memo'

    subject = fields.Char(string="Subject")

    date = fields.Date(string="Date", required=False, )
    memo_content = fields.HTML(string="",  )


