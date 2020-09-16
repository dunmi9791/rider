# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Vehicle(models.Model):
    _name = 'vehicles.rider'
    _rec_name = 'chassis_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_type = fields.Many2one(comodel_name="vehicletype.rider", string="Vehicle Type")
    vehicle_make = fields.Many2one(comodel_name="vehiclemake.rider", string="Vehicle Make")
    vehicle_model = fields.Many2one(comodel_name="vehiclemodel.rider", string="Vehicle Model")
    vehicle_registration = fields.Char()
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False,
                                track_visibility=True, trace_visibility='onchange', )
    chassis_no = fields.Char(string="Chassis Number", track_visibility=True, trace_visibility='onchange',)
    jobcard_ids = fields.One2many(comodel_name="servicerequest.rider", inverse_name="vehicle_id", string="", required=False, )



class VehicleType(models.Model):
    _name = 'vehicletype.rider'

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

