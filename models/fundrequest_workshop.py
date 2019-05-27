# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FundRequestWorkshop(models.Model):
    _name = 'fundrequestw.rider'
    _inherit = ['mail.thread']
    _rec_name = 'request_no'

    _description = 'Fund request workshop'

    date = fields.Date(string="Date", required=False, readonly=True, states={'draft': [('readonly', False)]})
    request_no = fields.Char(string="Request Number", requires=False, readonly=True, states={'draft': [('readonly', False)]})
    programme_id = fields.Many2one(comodel_name="programme", string="Programme ID", required=False, readonly=True, states={'draft': [('readonly', False)]})
    jobcard_id = fields.Many2one(comodel_name="servicerequest.rider", string="Job Card ref", required=False, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(string="", selection=[('draft', 'draft'), ('Requested', 'Requested'), ('Approved', 'Approved'), ('Rejected', 'Rejected'),], required=False, copy=False, default='draft', readonly=True, track_visibility='onchange', )
    operations = fields.One2many(
        'fundrequest.partsline', 'fundrequest_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)]})
    part_qty = fields.Float(string="Quantity",  required=False, )
    amount_total = fields.Float('Total', compute='_amount_total', store=True)

    @api.one
    @api.depends('operations.price_subtotal',)
    def _amount_total(self):

        self.amount_total = sum(operation.price_subtotal for operation in self.operations)

    @api.multi
    def workshop_fund_request(self):
        self.state = 'Requested'

    @api.multi
    def workshop_fund_approve(self):
        self.state = 'Approved'

    @api.multi
    def workshop_fund_reject(self):
        self.state = 'Rejected'

class Parts(models.Model):
    _name = 'parts.rider'
    _rec_name = 'name'

    _description = 'Parts'

    name = fields.Char(string="Name")
    description = fields.Char(string="Description", required=False, )
    cost = fields.Float(string=" Unit Cost",  required=False, )




class FundrequestLine(models.Model):
    _name = 'fundrequest.partsline'

    _description = 'Parts request line'

    name = fields.Text(string='Description', required=False)
    fundrequest_id = fields.Many2one(comodel_name="fundrequestw.rider", index=True, ondelete='cascade')
    parts_id = fields.Many2one('parts.rider', string='Parts',
                                 ondelete='restrict', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')], 'Status', default='draft',
        copy=False, readonly=True, required=True, )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)

    @api.one
    @api.depends('cost', 'fundrequest_id', 'quantity', 'name', )
    def _compute_price_subtotal(self):
        self.price_subtotal = self.cost * self.quantity

    quantity = fields.Float(string="Quantity", required=False, default=1.0, )
    cost = fields.Float(string=" Unit Cost", required=False, )






