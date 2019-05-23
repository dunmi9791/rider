# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Orders(models.Model):
    _name = 'order.rider'
    _rec_name = 'name'

    _description = 'orders'

    name = fields.Char()
    partner_id = fields.Many2one(comodel_name="partner.rider", string="Partner", required=False, )
    order_type = fields.Selection(string="Order Type", selection=[('Round', 'Round'), ('Retrieval', 'Retrieval'), ('PCR', 'PCR'), ('DOD', 'DOD'), ], required=False, )
    order_details = fields.Text(string="Order Details", required=False, )



