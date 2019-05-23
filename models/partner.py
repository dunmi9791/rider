# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Partner(models.Model):
    _name = 'partner.rider'
    _rec_name = 'name'
    _description = 'program partners'

    name = fields.Char()


