# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import date


class CashRequisition(models.Model):
    _name = 'cashrequisition.rider'
    _description = 'cash requisition'
    _inherit = ['mail.thread']

    date = fields.Date(string="Date", required=False, default=date.today(),)
    amount_words = fields.Char(string="Amount in Words", required=False, )
    amount_figures = fields.Float(string="Amount in Figures",  required=False, )
    payable = fields.Many2one(string="Payable to", comodel_name="res.users", required=False, )
    ref = fields.Many2one(string="Reference Document", comodel_name="fundrequestw.rider",  ondelete='restrict', required=False,)
    details = fields.Text(string="Details", required=False, )
    cash_no = fields.Char(string="Cash Requisition No.", default=lambda self: self.env['ir.sequence'].next_by_code('increment_cash_request'), requires=False, readonly=True, trace_visibility='onchange',)
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

