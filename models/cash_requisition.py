# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import date


class CashRequisition(models.Model):
    _name = 'cashrequisition.rider'
    _description = 'cash requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string="Date", required=False, default=date.today(),)
    amount_words = fields.Char(string="Amount in Words", required=False, )
    amount_figures = fields.Float(string="Amount in Figures",  required=False, )
    payable = fields.Many2one(string="Payable to", comodel_name="res.users", required=False, )
    ref = fields.Many2one(string="Reference Document", comodel_name="fundrequestw.rider",  ondelete='restrict', required=False,)
    ref2 = fields.Many2one(string="Reference Document exp", comodel_name="expense.rider", ondelete='restrict',
                          required=False, )
    details = fields.Text(string="Details", required=False, )
    cash_no = fields.Char(string="Cash Requisition No.", default=lambda self: _('New'), requires=False, readonly=True, trace_visibility='onchange',)
    state = fields.Selection(string="", selection=[('Requested', 'Requested'), ('Authorised', 'Authorised'), ('Processed', 'Processed'), ('Received', 'Received'), ('Canceled', 'Canceled'), ], required=False, default='Requested', track_visibility='onchange', )

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('Requested', 'Authorised'),
                   ('Requested', 'Canceled'),
                   ('Authorised', 'Processed'),
                   ('Authorised', 'Canceled'),
                   ('Processed', 'Received'), ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for cash in self:
            if cash.is_allowed_transition(cash.state, new_state):
                cash.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (cash.state, new_state)
                raise UserError(msg)

    @api.multi
    def authorise(self):
        self.change_state('Authorised')

    @api.multi
    def process(self):
        self.change_state('Processed')

    @api.multi
    def receive(self):
        self.change_state('Received')

    @api.multi
    def cancel(self):
        self.change_state('Canceled')



    @api.model
    def create(self, vals):
        if vals.get('cash_no', _('New')) == _('New'):
            vals['cash_no'] = self.env['ir.sequence'].next_by_code('increment_cash_request') or _('New')
        result = super(CashRequisition, self).create(vals)
        return result

class FundClassification(models.Model):
    _name = 'fund.classification'
    _rec_name = 'name'
    _description = 'Fund and expense classification'

    name = fields.Char()

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Classification name already exists !"),
    ]


class ExpenseRequest(models.Model):
    _name = 'expense.rider'
    _rec_name = 'exp_no'
    _description = 'staff expense request and reconciliation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    exp_no = fields.Char(string="Expense Number",
                         default=lambda self: _('New'),
                         requires=False, readonly=True, )
    date = fields.Date(string="Date", required=False, default=date.today(), readonly=True, states={'draft': [('readonly', False)]}, )
    memo_to = fields.Many2one(comodel_name="res.users", string="TO", domain=lambda self: [( "groups_id", "=", self.env.ref( "rider.group_approverequest_group" ).id )])
    copy_to = fields.Many2many(comodel_name="res.users", string="CC")
    subject = fields.Char(string="Subject", required=False, readonly=True, states={'draft': [('readonly', False)]},)
    request_from = fields.Many2one(comodel_name="res.users", string="From", readonly=True, default=lambda self: self.env.user)
    expenses = fields.One2many(
        'exprequest.expline', 'exprequest_id', 'Expenses',
        copy=True, readonly=True, states={'draft': [('readonly', False)]}, )
    expended = fields.One2many(
        'expended.expline', 'expended_id', 'Expenses',
        copy=True, readonly=True, states={'disburse': [('readonly', False)]},)
    amount_total = fields.Float('Total Requested/Approved', compute='_amount_total', store=True)
    state = fields.Selection(string="",
                             selection=[('draft', 'draft'), ('Requested', 'Requested'), ('Unit Head Approve', 'Unit Approval'),
                                        ('Fin Approve', 'Fin Approved'), ('requirecd', 'Awaiting CD Approval'),
                                        ('cdapprove', 'CD Approved'), ('disburse', 'disbursed'),
                                        ('reconcile', 'Submitted for reconciliation'), ('Rejected', 'Rejected'),
                                        ('fin reconcile', 'Reconciled')], required=False,
                             copy=False, default='draft', readonly=True, track_visibility='onchange', )
    expended_total = fields.Float('Total Spent', compute='_expended_total')
    balance = fields.Float('Amount Reimbursed/Returned', compute='_balance')
    department = fields.Selection(string="Department",
                                  selection=[('sampletransport', 'Sample Transport'), ('supplychain', 'Supply Chain'), ('finance', 'Finance'),
                                             ('humanresource', 'Human Resource'), ('workshop', 'Workshop'), ('admin', 'Admin'), ('it', 'IT'),], required=True,)
    mode_of_disburse = fields.Selection(string="Mode of Disbursement", selection=[('cash', 'Cash'), ('transfer', 'Transfer'),],
                                        states={'Fin Approve': [('required', True)]})
    classification = fields.Many2one(string="Expense Classification", comodel_name="fund.classification")
    flag = fields.Boolean(string="", )

    @api.model
    def create(self, vals):
        res = super(ExpenseRequest, self).create(vals)
        if res.copy_to:
            for copy in res.copy_to:
                vals['message_follower_ids'] += self.env['mail.followers']._add_follower_command(self._name, [], {copy.id}, {})[
        0]
                return res


    @api.one
    @api.depends('expenses.price_subtotal', )
    def _amount_total(self):
        self.amount_total = sum(expense.price_subtotal for expense in self.expenses)


    @api.one
    @api.depends('expenses.price_subtotal', )
    def _expended_total(self):
        self.expended_total = sum(expend.amount for expend in self.expended)

    @api.one
    def _balance(self):
        self.balance = self.amount_total - self.expended_total

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'Requested'),
                   ('Requested', 'Unit Head Approve'),
                   ('Requested', 'Rejected'),
                   ('Requested', 'draft'),
                   ('Unit Head Approve', 'Fin Approve'),
                   ('Unit Head Approve', 'Rejected'),
                   ('Fin Approve', 'Rejected'),
                   ('Fin Approve', 'disburse'),
                   ('Fin Approve', 'requirecd'),
                   ('requirecd', 'cdapprove'),
                   ('requirecd', 'Rejected'),
                   ('cdapprove', 'disburse'),
                   ('disburse', 'reconcile'),
                   ('reconcile', 'fin reconcile'),
                   ('reconcile', 'disburse'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for request in self:
            if request.is_allowed_transition(request.state, new_state):
                request.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (request.state, new_state)
                raise UserError(msg)

    @api.multi
    def expense_request(self):
        self.change_state('Requested')

    @api.multi
    def unit_expense_approve(self):
        self.change_state('Unit Head Approve')

    @api.multi
    def expense_fin_approve(self):
        self.change_state('Fin Approve')

    @api.multi
    def expense_reject(self):
        self.change_state('Rejected')

    @api.multi
    def expensefin_reject(self):
        self.change_state('Rejected')

    @api.multi
    def expense_disburse(self):
        self.change_state('disburse')

    @api.multi
    def expense_reconcile(self):
        self.change_state('reconcile')

    @api.multi
    def require_cd(self):
        self.change_state('requirecd')

    @api.multi
    def cd_approve(self):
        self.change_state('cdapprove')

    @api.multi
    def reset_draft(self):
        self.change_state('draft')

    @api.multi
    def fin_reconcile(self):
        self.change_state('fin reconcile')

    @api.multi
    def reject_reconcile(self):
        self.change_state('disburse')

    @api.model
    def create(self, vals):
        if vals.get('exp_no', _('New')) == _('New'):
            vals['exp_no'] = self.env['ir.sequence'].next_by_code('increment_expense') or _('New')
            res = super(ExpenseRequest, self).create(vals)
            for rec in res:
                if rec.copy_to:
                    partner_ids = []
                    for copy in rec.copy_to:
                        if copy.partner_id and copy.partner_id.email:
                            partner_ids.append(copy.partner_id.id)
                    if partner_ids:
                        rec.message_subscribe(partner_ids, None)
            return res




class ExpenserequestLine(models.Model):
    _name = 'exprequest.expline'

    _description = 'Expense line items'

    name = fields.Char()
    exprequest_id = fields.Many2one(comodel_name="expense.rider", index=True, ondelete="cascade")
    item_id = fields.Many2one(comodel_name="expense.item", string="Item", required=True, ondelete="restrict", index=True)
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", required=False, default=1.0, )
    cost = fields.Float(string=" Unit Cost", required=False, )
    price_subtotal = fields.Float('Subtotal', compute='_compute_price_subtotal', store=True, digits=0)
    date = fields.Date(string="Date", required=False, related='exprequest_id.date')

    @api.one
    @api.depends('cost', 'exprequest_id', 'quantity', 'name', )
    def _compute_price_subtotal(self):
        self.price_subtotal = self.cost * self.quantity

class ExpenseItem(models.Model):
    _name = 'expense.item'
    _rec_name = 'name'
    _description = 'Items'

    name = fields.Char(string="Item")
    active = fields.Boolean('active', default=True)


    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Item already exist')
    ]

class Expended(models.Model):
    _name = 'expended.expline'

    _description = 'Actual expense'

    name = fields.Char()
    expended_id = fields.Many2one(comodel_name="expense.rider", index=True, ondelete="cascade")
    item_id = fields.Many2one(comodel_name="expense.item", string="Item", ondelete="restrict", index=True)
    remark = fields.Char(string="Remark")
    amount = fields.Float(string="Amount Spent", required=False, )
    receipt = fields.Binary(string="Receipt",)


class ExpenseRequestFlag(models.TransientModel):
    """
    This wizard will flag expense request to attend to later
    """

    _name = "expense.request.flag"
    _description = "Flag selected expense request"

    @api.multi
    def expense_flag(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['expense.rider'].browse(active_ids):
            record.flag = True

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def expense_unflag(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['expense.rider'].browse(active_ids):
            record.flag = False

        return {'type': 'ir.actions.act_window_close'}





