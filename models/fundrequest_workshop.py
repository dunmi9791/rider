# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FundRequestWorkshop(models.Model):
    _name = 'fundrequestw.rider'

    _description = 'Fund request workshop'

    date = fields.Date(string="Date", required=False, )
    request_no = fields.Char(string="Request Number" , requires=False, )
    programme_id = fields.Many2one(comodel_name="programme", string="Programme ID", required=False, )
    jobcard_id = fields.Many2one(comodel_name="servicerequest.rider", string="Job Card ref", required=False, )
    state = fields.Selection(string="", selection=[('draft', 'draft'), ('Requested', 'Requested'), ('Approved', 'Approved'), ], required=False, copy=False, default='draft', readonly=True, track_visibility='onchange', )
    operations = fields.One2many(
        'parts.rider', 'fundrequest_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)]})

class Parts(models.Model):
    _name = 'parts.rider'

    _description = 'Parts'

    name = fields.Char(string="Name")
    description = fields.Char(string="Description", required=False, )
    cost = fields.Float(string=" Unit Cost",  required=False, )
    fundrequest_id = fields.Many2one(comodel_name="fundrequestw.rider", index=True, ondelete='cascade')
    quantity = fields.Float(string="Quantity",  required=False, default=1.0, )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)

    @api.one
    @api.depends('cost', 'fundrequestw_id', 'quantity', 'name',)
    def _compute_price_subtotal(self):

        self.price_subtotal = self.cost*self.quantity




