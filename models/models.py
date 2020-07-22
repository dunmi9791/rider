# -*- coding: utf-8 -*-
from typing import List, Any

from odoo import models, fields, api
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ServiceRequest(models.Model):
    _name = 'servicerequest.rider'
    _rec_name = 'jobcard_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "checkin_date desc, id desc"

    vehicle_id = fields.Many2one('vehicles.rider', string='Vehicle Chassis No.', required=True)
    vehicle_reg_id = fields.Many2one('vehicles.rider', string='Registration Number', readonly=True,
                                          states={'check-in': [('readonly', False)], 'Tech Eval': [('readonly', False)],
                                                  'Confirm': [('readonly', False)]},
                                          help="Registration number.")
    vehicle_reg = fields.Char(string='Registration Number', related='vehicle_id.vehicle_registration', readonly=True,

                                          help="Registration number.")
    client = fields.Many2one(string='Client', related='vehicle_id.client_id', readonly=True, store=True,
                             help="Registration number.")
    checkin_date = fields.Datetime(string="Check-in Date/Time", required=False, default=datetime.now())
    checkout_date = fields.Datetime(string="Check-out Date/Time", required=False, )
    electrics_ta = fields.Selection(string="Electronic Assessment", selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
                                     required=False, )
    suspension_ta = fields.Selection(string="Suspension",selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
                                     required=False, )
    engine_ta = fields.Selection(string="Engine Assessment",selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
                                     required=False, )
    bodywork_ta = fields.Selection(string="Body Work Assessment",selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
                                        required = False, )
    interior_ta = fields.Selection(string="Interior Assessment",
                                     selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
                                     required=False, )
    tyres_ta = fields.Selection(string="Tyres Assessment",
                                     selection=[('1', '1. Very poor condition'), ('2', '2. poor condition'), ('3', '3.fair condition'), ('4', '4. good condition'), ('5', '5. Excellent condition'), ],
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
    state = fields.Selection(string="", selection=[('check-in', 'check-in'), ('Tech Eval', 'Tech eval completed'),
                                                   ('customer approve', 'Awaiting Customer Approval'),
                                                   ('Confirm', 'Confirmed'), ('parts release', 'parts released'),
                                                   ('quality check', 'quality checked'), ('Checked out', 'Checked out'),
                                                   ('cancel', 'Canceled'),
                                                   ], default='check-in', required=False, track_visibility=True,
                             trace_visibility='onchange', )
    jobcard_no = fields.Char(string="Jobcard Number",
                             default=lambda self: _('New'),
                             requires=False, readonly=True, )
    operations = fields.One2many(
        'jobcard.partsline', 'servicerequest_id', 'Parts',
        copy=True, readonly=True, states={'check-in': [('readonly', False)], 'Tech Eval': [('readonly', False)]})
    odometer = fields.Char(string="Odometer Reading", required=True, )
    partsline_id = fields.Many2one(comodel_name="jobcard.partline", string="", required=False, )
    fundrequest_id = fields.Many2one('fundrequestw.rider', string="", required=False, )
    fundrequest_ids = fields.Many2many(comodel_name="fundrequestw.rider",string='Fund request', compute="_get_fundrequest", readonly=True, copy=False )
    parts_ids = fields.Integer(string="", required=False, compute="get_parts_id",)
    workshop = fields.Selection(string="Workshop", selection=[('abuja', 'Abuja'), ('lagos', 'Lagos'),
                                                      ('enugu', 'Enugu'), ('others', 'Others')], default='abuja', required=False, )


    @api.multi
    def get_parts_id(self):
        parts = self.operations.parts_id.ids
        parts_ids = {
            'operations': [(0, 0, {parts}), (0, 0, {parts}), ...],
        }
        return parts_ids

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('check-in', 'Tech Eval'),
                   ('check-in', 'customer approve'),
                   ('check-in', 'Confirm'),
                   ('check-in', 'cancel'),
                   ('Tech Eval', 'customer approve'),
                   ('Tech Eval', 'Confirm'),
                   ('Tech Eval', 'cancel'),
                   ('customer approve', 'Confirm'),
                   ('customer approve', 'cancel'),
                   ('Confirm', 'parts release'),
                   ('Confirm', 'cancel'),
                   ('parts release', 'quality check'),
                   ('quality check', 'Checked out')]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for job in self:
            if job.is_allowed_transition(job.state, new_state):
                job.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (job.state, new_state)
                raise UserError(msg)


    @api.multi
    def technician_complete(self):
        self.change_state('Tech Eval')

    @api.multi
    def customer_approval(self):
        self.change_state('customer approve')

    @api.multi
    def unitmanager_approve(self):
        self.change_state('Confirm')

    @api.multi
    def parts_released(self):
        self.change_state('parts release')


    @api.multi
    def quality_check(self):
        self.change_state('quality check')

    @api.multi
    def check_out(self):
        self.change_state('Checked out')

    @api.multi
    def cancel(self):
        self.change_state('cancel')

    def _track_subtype(self, init_values):
        # init_values contains the modified fields' values before the changes
        #
        # the applied values can be accessed on the record as they are already
        # in cache
        self.ensure_one()
        if 'state' in init_values and self.state == 'Unit Manager parts approved':
            return 'rider.jc_state_change'  # Full external id
        return super(ServiceRequest, self)._track_subtype(init_values)

    def _track_subtype(self, init_values):
        if 'state' in init_values:
            return 'mail.mt_comment'
        return False

    @api.multi
    def write(self, vals):
        if vals.get('state'):
            if vals.get('state') == 'Confirm':
                lines = []
                for line in self.operations:
                    fund_line = {
                        'parts_id': line.parts_id.id,
                        'quantity': line.quantity,
                    }

                    lines.append((0, 0, fund_line))
                fund_dict = {
                        'jobcard_id': self.id,
                        'operations': lines,
                    }
                record = self.env['fundrequestw.rider']
                record.create(fund_dict)

                return super(ServiceRequest, self).write(vals)
            else:
                return super(ServiceRequest, self).write(vals)
        else:
            return super(ServiceRequest, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('jobcard_no', _('New')) == _('New'):
            vals['jobcard_no'] = self.env['ir.sequence'].next_by_code('increment_jobcard') or _('New')
        result = super(ServiceRequest, self).create(vals)
        return result




class JobcardParts(models.Model):
    _name = 'jobcard.partsline'

    _description = 'Parts Required used'

    name = fields.Text(string='Description', required=False)
    servicerequest_id = fields.Many2one(comodel_name="servicerequest.rider", index=True, ondelete='cascade')
    parts_id = fields.Many2one('product.product', string='Parts',
                               ondelete='restrict', index=True)
    quantity = fields.Integer(string="Quantity", required=False, )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')], 'Status', default='draft',
        copy=False, readonly=True, required=True, )
    fundrequestlines_ids = fields.Many2many(comodel_name="fundrequest.partsline",
                                            relation="jobcard_line_fundrequest_rel",
                                            column1="servicerequest_id", column2="fundrequest_id",
                                            string="Fundrequest lines", copy=False)
    fundrequest_id = fields.Many2one(comodel_name="fundrequestw.rider", string="fundrequest", required=False, related="servicerequest_id.fundrequest_id", readonly=True )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)

    @api.one
    @api.depends('cost', 'fundrequest_id', 'quantity', 'name', )
    def _compute_price_subtotal(self):
        self.price_subtotal = self.cost * self.quantity

    cost = fields.Float(string=" Unit Cost", required=False, )

    @api.multi
    def invoice_line_create(self, fundrequest_id):
        """ Create an invoice line. The quantity to invoice can be positive (invoice) or negative (refund).

            .. deprecated:: 12.0
                Replaced by :func:`invoice_line_create_vals` which can be used for creating
                `account.invoice.line` records in batch

            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """
        return self.env['fundrequest.partsline'].create(
            self.fundrequest_line_create_vals(fundrequest_id))

    def fundrequest_line_create_vals(self, fundrequest_id):
        """ Create an invoice line. The quantity to invoice can be positive (invoice) or negative
            (refund).

            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns list of dict containing creation values for account.invoice.line records
        """
        vals_list = []

        for line in self:
            vals = line._prepare_fundrequest_line()
            vals.update({'fundrequest_id': fundrequest_id, 'jobcard_line_ids': [(6, 0, [line.id])]})
            vals_list.append(vals)
        return vals_list

    @api.multi
    def _prepare_fundrequest_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}

        res = {

            'sequence': self.sequence,

            'parts_id': self.parts_id.id or False,

        }
        return res

    @api.multi
    def prepare_lines(self):
        lines_dict = {
            'fundrequest_id': self.fundrequest_id,
            'parts_id': [(0, 0, self.parts_id)],
            'state': self.state,
        }
        return self.env['fundrequest.partsline'].create(lines_dict)

class JobcardQuote(models.Model):
    _inherit = 'sale.order'

    jobcard_id = fields.Many2one(comodel_name="servicerequest.rider", string="Job Card", required=False, )









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
