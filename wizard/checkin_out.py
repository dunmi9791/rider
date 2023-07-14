# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _


class CheckinVehicle(models.TransientModel):
    _name = 'riders.checkin.vehicle'
    _description = 'Checkin Vehicle'

    vehicle_id = fields.Many2one(comodel_name='vehicles.rider', string='Vehicle')
    millage = fields.Char(string='Millage')
    driver_id = fields.Many2one(comodel_name='res.partner', string='Driver')
    checkin_date = fields.Datetime(string="Check-in Date/Time", required=False, default=fields.Datetime.now)
    jack = fields.Boolean(string='Jack')
    spare_tyre = fields.Boolean(string='Spare Tyre')
    wheel_spanner = fields.Boolean(string='Wheel Spanner')
    triangle = fields.Boolean(string='Triangle')
    fire_extinguisher = fields.Boolean(string='Fire Extinguisher')
    first_aid_kit = fields.Boolean(string='First Aid Kit')
    tools = fields.Boolean(string='Tools')
    others = fields.Char(string='Others')
    jobcard_id = fields.Many2one(comodel_name='servicerequest.rider', string='Jobcard')



    def checkin_vehicle(self):
        for rec in self:
            checkin_params = []
            vals = {'vehicle_id': rec.vehicle_id.id,
                    'millage': rec.millage,
                    'driver_id': rec.driver_id.id,
                    'jack': rec.jack,
                    'spare_tyre': rec.spare_tyre,
                    'wheel_spanner': rec.wheel_spanner,
                    'triangle': rec.triangle,
                    'fire_extinguisher': rec.fire_extinguisher,
                    'first_aid_kit': rec.first_aid_kit,
                    'tools': rec.tools,
                    'in_out': 'in',
                    'jobcard_id': rec.jobcard_id.id,
                    'checkin_date': rec.checkin_date,
                    'others': rec.others,
                    }
            checkin_params.append(vals)
            self.env['vehicle.checkin'].create(checkin_params)
            self.env['vehicle.millage'].create({'vehicle_id': rec.vehicle_id.id,'millage': rec.millage, 'date': rec.checkin_date})
            rec.jobcard_id.vehicle_in = True


class CheckoutVehicle(models.TransientModel):
    _name = 'riders.checkout.vehicle'
    _description = 'Checkout Vehicle'

    vehicle_id = fields.Many2one(comodel_name='vehicles.rider', string='Vehicle')
    millage = fields.Char(string='Millage')
    driver_id = fields.Many2one(comodel_name='res.partner', string='Driver')
    checkout_reason = fields.Selection(
        string='Checkout reason',
        selection=[('job_complete', 'Job complete'),
                   ('seek_approval', 'Seek Approval'),
                   ('others', 'Others'),],
        required=False, )

    checkout_date = fields.Datetime(string="Check-in Date/Time", required=False, default=fields.Datetime.now)
    jack = fields.Boolean(string='Jack')
    spare_tyre = fields.Boolean(string='Spare Tyre')
    wheel_spanner = fields.Boolean(string='Wheel Spanner')
    triangle = fields.Boolean(string='Triangle')
    fire_extinguisher = fields.Boolean(string='Fire Extinguisher')
    first_aid_kit = fields.Boolean(string='First Aid Kit')
    tools = fields.Boolean(string='Tools')
    others = fields.Char(string='Others')
    jobcard_id = fields.Many2one(comodel_name='servicerequest.rider', string='Jobcard')



    def checkout_vehicle(self):
        for rec in self:
            checkout_params = []
            vals = {'vehicle_id': rec.vehicle_id.id,
                    'millage': rec.millage,
                    'driver_id': rec.driver_id.id,
                    'checkout_reason': rec.checkout_reason,
                    'jack': rec.jack,
                    'spare_tyre': rec.spare_tyre,
                    'wheel_spanner': rec.wheel_spanner,
                    'triangle': rec.triangle,
                    'fire_extinguisher': rec.fire_extinguisher,
                    'first_aid_kit': rec.first_aid_kit,
                    'tools': rec.tools,
                    'in_out': 'out',
                    'jobcard_id': rec.jobcard_id.id,
                    'checkin_date': rec.checkout_date,
                    'others': rec.others,
                    }
            checkout_params.append(vals)
            self.env['vehicle.checkin'].create(checkout_params)
            self.env['vehicle.millage'].create({'vehicle_id': rec.vehicle_id.id,'millage': rec.millage, 'date': rec.checkout_date})
            rec.jobcard_id.vehicle_in = False
