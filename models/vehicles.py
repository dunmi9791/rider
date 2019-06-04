# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Vehicle(models.Model):
    _name = 'vehicles.rider'

    vehicle_type = fields.Char()
    vehicle_registration = fields.Char()
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False, )
