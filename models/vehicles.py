# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Vehicle(models.Model):
    _name = 'vehicles.rider'

    vehicle_type = fields.Many2one(comodel_name="vehichletype.rider", string="Vehicle Type")
    vehicle_make = fields.Many2one(comodel_name="vehichlemake.rider", string="Vehicle Make")
    vehicle_model = fields.Many2one(comodel_name="vehichlemodel.rider", string="Vehicle Model")
    vehicle_registration = fields.Char()
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False, )



class VehicleType(models.Model):
    _name = 'vehicletype.rider'
    _rec_name = 'name'
    _description = 'Vehicle Type'

    name = fields.Char()

class VehicleMake(models.Model):
    _name = 'vehiclemake.rider'
    _rec_name = 'name'
    _description = 'Vehicle Make'

    name = fields.Char()


class VehicleModel(models.Model):
    _name = 'vehiclemodel.rider'
    _rec_name = 'name'
    _description = 'Vehicle Model'

    name = fields.Char()

