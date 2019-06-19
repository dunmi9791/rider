# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Memo(models.Model):
    _name = 'memo.rider'
    _rec_name = 'name'
    _description = 'New Description'

    name = fields.Char(string="Memo Subject", required=False,)

    date = fields.Date(string="", required=False, )
