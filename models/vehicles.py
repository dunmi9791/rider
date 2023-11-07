# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Vehicle(models.Model):
    _name = 'vehicles.rider'
    _rec_name = 'chassis_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_type = fields.Many2one(comodel_name="vehicletype.rider", string="Vehicle Type", track_visibility=True, trace_visibility='onchange',)
    vehicle_make = fields.Many2one(comodel_name="vehiclemake.rider", string="Vehicle Make", track_visibility=True, trace_visibility='onchange',)
    vehicle_model = fields.Many2one(comodel_name="vehiclemodel.rider", string="Vehicle Model", track_visibility=True, trace_visibility='onchange',)
    vehicle_registration = fields.Char()
    vehicle_year = fields.Selection(selection='_get_years', string='Year', store=True)
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False,
                                track_visibility=True, trace_visibility='onchange', )
    chassis_no = fields.Char(string="Chassis Number", track_visibility=True, trace_visibility='onchange',)
    jobcard_ids = fields.One2many(comodel_name="servicerequest.rider", inverse_name="vehicle_id", string="", required=False, )
    millage_ids = fields.One2many(comodel_name="vehicle.millage", inverse_name="vehicle_id", string="Millage")
    vehicle_full_name = fields.Char(string="Vehicle", compute="_vehicle_name", store=True)
    odometers = fields.Char(string='Latest Odometer', compute='_compute_latest_millage')

    @api.one
    @api.depends('vehicle_make', 'vehicle_model', 'vehicle_year')
    def _vehicle_name(self):
        for record in self:
            record['vehicle_full_name'] = (record.vehicle_make.name or '') + ' ' + (record.vehicle_model.name or '') + ' ' +(record.vehicle_year or '')

    @api.multi
    @api.depends('')
    def _get_years(self):
        year_list = []
        for i in range(1900, 2070):
            year_list.append((i, str(i)))
        return year_list

    @api.depends('millage_ids')
    def _compute_latest_millage(self):
        for record in self:
            valid_millages = record.millage_ids.filtered(lambda r: r.date)
            if valid_millages:
                latest_millage = max(valid_millages, key=lambda r: r.date)
                record.odometers = latest_millage.millage if latest_millage else 0.0
class VehicleMillage(models.Model):
    _name = 'vehicle.millage'
    _description = 'Vehicle Millage history'

    date = fields.Date(
        string='Date',
        required=False)
    millage = fields.Char()
    vehicle_id = fields.Many2one(
        comodel_name='vehicles.rider',
        string='Vehicle_id',
        required=True)

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


class VehicleCheckin(models.Model):
    _name = 'vehicle.checkin'
    _description = 'Vehicle Checkin'

    vehicle_id = fields.Many2one(comodel_name='vehicles.rider', string='Vehicle')
    millage = fields.Char(string='Millage')
    driver_id = fields.Many2one(comodel_name='res.partner', string='Driver')
    checkin_date = fields.Datetime(string="Check-in Date/Time", required=False, )
    jack = fields.Boolean(string='Jack')
    spare_tyre = fields.Boolean(string='Spare Tyre')
    wheel_spanner = fields.Boolean(string='Wheel Spanner')
    triangle = fields.Boolean(string='Triangle')
    fire_extinguisher = fields.Boolean(string='Fire Extinguisher')
    first_aid_kit = fields.Boolean(string='First Aid Kit')
    others = fields.Char(string='Others')
    in_out = fields.Selection(
        string='In_out',
        selection=[('in', 'In'),
                   ('out', 'Out'), ],
        required=False, )
    checkout_reason = fields.Selection(
        string='Checkout reason',
        selection=[('job_complete', 'Job complete'),
                   ('seek_approval', 'Seek Approval'),
                   ('others', 'Others'), ],
    required = False, )
    jobcard_id = fields.Many2one(comodel_name='servicerequest.rider', string='Jobcard')


