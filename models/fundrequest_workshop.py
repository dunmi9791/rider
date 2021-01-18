# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError
from odoo.tools.translate import _

class FundRequestWorkshop(models.Model):
    _name = 'fundrequestw.rider'
    _rec_name = 'request_no'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    _description = 'Fund request workshop'

    date = fields.Date(string="Date", default=date.today(), required=False, readonly=True, states={'draft': [('readonly', False)]})
    request_no = fields.Char(string="Request Number", default=lambda self: _('New'), requires=False, readonly=True,
                             trace_visibility='onchange',)
    programme_id = fields.Many2one(comodel_name="programme.rider", string="Programme ID", required=False, readonly=True, states={'draft': [('readonly', False)]})
    jobcard_id = fields.Many2one(comodel_name="servicerequest.rider", string="Job Card ref", required=False, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(string="", selection=[('draft', 'draft'), ('Requested', 'Requested'), ('PD Approve', 'PD Approval'), ('Fin Approve', 'Fin Approved'),('requirecd', 'Awaiting CD Approval'),
                                                   ('cdapprove', 'CD Approved'), ('process', 'Processed'), ('Rejected', 'Rejected'),], required=False, copy=False, default='draft', readonly=True, track_visibility='onchange', )
    operations = fields.One2many(
        'fundrequest.partsline', 'fundrequest_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)]},)
    part_qty = fields.Float(string="Quantity",  required=False, )
    amount_total = fields.Float('Total', compute='_amount_total', store=True)
    client = fields.Many2one(string='Client', related='jobcard_id.client', readonly=True, store=True,
                             help="Registration number.")
    classification = fields.Many2one(string="Expense Classification", comodel_name="fund.classification")
    debit_account_id = fields.Many2one(string="Debit account", comodel_name='account.account')
    credit_account_id = fields.Many2one(string='Credit Account', comodel_name='account.account')
    journal_id = fields.Many2one(string='Journal', comodel_name='account.journal')

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'Requested'),
                   ('Requested', 'PD Approve'),
                   ('Requested', 'Rejected'),
                   ('PD Approve', 'Fin Approve'),
                   ('Fin Approve', 'process'),
                   ('Fin Approve', 'requirecd'),
                   ('requirecd', 'cdapprove'),
                   ('cdapprove', 'process'),
                   ('PD Approve', 'Rejected'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for fund in self:
            if fund.is_allowed_transition(fund.state, new_state):
                fund.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (fund.state, new_state)
                raise UserError(msg)


    # @api.model_create_multi
    # def create(self, vals):
    #     result = super(FundRequestWorkshop, self).create(vals)
    #     if result.jobcard_id:
    #         parts_id = result.jobcard_id.id
    #         parts = self.env['jobcard.partsline'].search([('servicerequest_id', '=', parts_id)])
    #         for line in parts:
    #             lines_dict = {
    #                 'state': line.state,
    #                 'parts_id': line.parts_id.id,
    #                 'quantity': line.quantity,
    #                 'fundrequest_id': result.id,
    #             }
    #
    #             self.env['fundrequest.partsline'].create(lines_dict)
    #             if vals.get('request_no', _('New')) == _('New'):
    #                 vals['request_no'] = self.env['ir.sequence'].next_by_code('increment_fund_request') or _('New')
    #         return result

    @api.model
    def create(self, vals):
        if vals.get('request_no', _('New')) == _('New'):
            vals['request_no'] = self.env['ir.sequence'].next_by_code('increment_fund_request') or _('New')
        result = super(FundRequestWorkshop, self).create(vals)
        return result









    @api.one
    @api.depends('operations.price_subtotal',)
    def _amount_total(self):

        self.amount_total = sum(operation.price_subtotal for operation in self.operations)

    @api.multi
    def workshop_fund_request(self):
        self.change_state('Requested')

    @api.multi
    def workshop_fund_approve(self):
        self.change_state('PD Approve')

    @api.multi
    def workshop_fund_fin_approve(self):
        self.change_state('Fin Approve')

    @api.multi
    def workshop_fund_reject(self):
        self.change_state('Rejected')

    @api.multi
    def workshop2_fund_reject(self):
        self.change_state('Rejected')

    @api.multi
    def require_cd(self):
        self.change_state('requirecd')

    @api.multi
    def cd_approve(self):
        self.change_state('cdapprove')

    @api.multi
    def process(self):
        credit_vals = []
        for credit_val in self.operations:
            val = {
                'name': credit_val.parts_id.name,
                'credit': abs(credit_val.price_subtotal),
                'debit': 0.0,
                'account_id': self.credit_account_id.id,
                'partner_id': credit_val.vendor_id.id,
                # 'tax_line_id': adjustment_type == 'debit' and self.tax_id.id or False,
        }
            credit_vals.append(val)
        debit_vals = {
            'name': self.request_no,
            'credit': 0.0,
            'debit': abs(self.amount_total),
            'account_id': self.debit_account_id.id,
            # 'tax_line_id': adjustment_type == 'credit' and self.tax_id.id or False,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': self.request_no,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), credit_vals]
        }
        move = self.env['account.move'].create(vals)
        self.change_state('process')


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
    parts_id = fields.Many2one('product.product', string='Parts',
                                 ondelete='restrict', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')], 'Status', default='draft',
        copy=False, readonly=True, required=True, )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)
    account_id = fields.Many2one('account.account', string='Account', ondelete='restrict', index=True)
    source = fields.Selection([
        ('store', 'store'),
        ('cash', 'cash'), ('transfer', 'Transfer')], string='Remark', required=True,)
    vendor_id = fields.Many2one('res.partner', string='Vendor',)
    @api.one
    @api.depends('cost', 'fundrequest_id', 'quantity', 'name', )
    def _compute_price_subtotal(self):
        self.price_subtotal = self.cost * self.quantity

    quantity = fields.Integer(string="Quantity", required=False, default=1.0, )
    cost = fields.Float(string=" Unit Cost", required=False, )
    jobcard_line_ids = fields.Many2many(comodel_name="jobcard.partsline",
                                     relation="jobcard_line_fundrequest_rel",
                                     column1="fundrequest_id", column2="servicerequest_id",
                                     string="Job Card lines", readonly=True, copy=False )
    client = fields.Many2one(string='Client', related='fundrequest_id.client', readonly=True, store=True,
                             help="Registration number.")


class PartsRequest(models.Model):
    _name = 'partsrequest.rider'
    _rec_name = 'request_no'
    _description = 'Parts request'
    _inherit = ['mail.thread']

    date = fields.Date(string="Date", default=date.today(), required=False, readonly=True,
                       states={'draft': [('readonly', False)]})
    request_no = fields.Char(string="Request Number",
                             default=lambda self: self.env['ir.sequence'].next_by_code('increment_parts_request'),
                             requires=False, readonly=True, )
    programme_id = fields.Many2one(comodel_name="programme.rider", string="Programme ID", required=False, readonly=True,
                                   states={'draft': [('readonly', False)]})
    jobcard_id = fields.Many2one(comodel_name="servicerequest.rider", string="Job Card ref", required=False,
                                 readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(string="",
                             selection=[('draft', 'draft'), ('Requested', 'Requested'), ('Approved', 'Approved'),
                                        ('Rejected', 'Rejected'), ], required=False, copy=False, default='draft',
                             readonly=True, track_visibility='onchange', )
    operations = fields.One2many(
        'partsrequest.partsline', 'partsrequest_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)]})
    part_qty = fields.Float(string="Quantity", required=False, )
    amount_total = fields.Float('Total', compute='_amount_total', store=True)

    @api.multi
    def workshop_parts_request(self):
        self.state = 'Requested'

    @api.multi
    def workshop_parts_approve(self):
        self.state = 'Approved'

    @api.multi
    def workshop_parts_reject(self):
        self.state = 'Rejected'


class PartsrequestLine(models.Model):
    _name = 'partsrequest.partsline'

    _description = 'Parts request line'

    name = fields.Text(string='Description', required=False)
    partsrequest_id = fields.Many2one(comodel_name="partsrequest.rider", index=True, ondelete='cascade')
    parts_id = fields.Many2one('product.product', string='Parts',
                               ondelete='restrict', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')], 'Status', default='draft',
        copy=False, readonly=True, required=True, )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)

    @api.one
    @api.depends('partsrequest_id', 'quantity', 'name', )
    def _compute_price_subtotal(self):
        self.price_subtotal = self.cost_supplier1 * self.quantity

    quantity = fields.Float(string="Quantity", required=False, default=1.0, )
    cost_supplier1 = fields.Float(string=" Unit Cost", required=False, )
    cost_supplier2 = fields.Float(string=" Unit Cost", required=False, )
    cost_supplier3 = fields.Float(string=" Unit Cost", required=False, )

    supplier1_id = fields.Many2one(comodel_name="res.partner", string="Supplier 1", required=False, )
    supplier2_id = fields.Many2one(comodel_name="res.partner", string="Supplier 2", required=False, )
    supplier3_id = fields.Many2one(comodel_name="res.partner", string="Supplier 3", required=False, )
    recommended = fields.Selection(string="Recommended Supplier", selection=[('supplier 1', 'supplier 1'), ('supplier 2', 'supplier 2'), ('supplier 3', 'supplier 3'), ], required=False, )


class Programme(models.Model):
    _name = 'programme.rider'
    _rec_name = 'name'
    _description = 'Programmes'

    name = fields.Char(string="Programme")














