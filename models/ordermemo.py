# -*- coding: utf-8 -*-

from odoo import models, fields, api

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="Memo Subject", required=False,)
    new_field = fields.HTML(string="",  )
    date = fields.Date(string="", required=False, )
