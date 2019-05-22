# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ServiceRequest(models.Model):
    _name = 'servicerequest.rider'

    vehicle_id = fields.Many2one('vehicles.rider')
    checkin_date = fields.Datetime(string="Check-in Date/Time", required=False, )
    checkout_date = fields.Datetime(string="Check-out Date/Time", required=False, )
    electrics_ta = fields.Selection(string="Electronic Assessment", selection=[('1', '1'), ('2', '2'),('3', '3'),('4', '4'), ('5', '5'), ], required=False, )
    suspension_ta = fields.Selection(string="Suspension Assessment",
                                     selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
                                     required=False, )
    engine_ta = fields.Selection(string="Engine Assessment",
                                     selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
                                     required=False, )
    bodywork_ta = fields.Selection(string="Body Work Assessment",
                                     selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
                                     required=False, )
    interior_ta = fields.Selection(string="Interior Assessment",
                                     selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
                                     required=False, )
    tyres_ta = fields.Selection(string="Tyres Assessment",
                                     selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ],
                                     required=False, )
    service_type = fields.Selection(string="Serivice Type", selection=[('Planned', 'Planned'), ('Accident', 'Accident'),('Breakdown', 'Breakdown'), ('Technical Problem', 'Technical Problem'), ('Demand Service','Demand service'), ('Return Job', 'Return Job'), ], required=False, )
    checkin_comment = fields.Text(string="Check-in Comment", required=False, )
    technical_comment = fields.Text(string="Description of work required identified br technical assessment", required=False, )
    spare_tyre = fields.Boolean(string="Spare Tyre",  )
    jack = fields.Boolean(string="Jack",  )
    wheel_spanner = fields.Boolean(string="Wheel Spanner",  )
    tools = fields.Boolean(string="Tools",  )
    caution_triangle = fields.Boolean(string="Caution Triangle",  )
    fire_extinguisher = fields.Boolean(string="Fire Extinguisher",  )
    state = fields.Selection(string="", selection=[('check-in', 'check-in'), ('Technician service completed', 'Technician service completed'), ('Unit Manager parts approved', 'Unit Manager parts approved'), ('store officer parts released', 'store officer parts released'), ('Unit manager quality check', 'Unit manager quality checked'), ('Checked out', 'Checked out'), ], default='check-in', required=False, )




    @api.multi
    def technician_complete(self):
        self.state = 'Technician service completed'

    

# class rider(models.Model):
#     _name = 'rider.rider'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100