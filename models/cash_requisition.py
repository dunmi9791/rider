# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CashRequisition(models.Model):
    _name = 'cashrequisition.rider'
    _description = 'cash requisition'

    date = fields.Date(string="Date", required=False, )
    amount_words = fields.Char(string="Amount in Words", required=False, )
    amount_figures = fields.Float(string="Amount in Figures",  required=False, )
    payable = fields.Char(string="Payable to", required=False, )
    details = fields.Text(string="Details", required=False, )
    state = fields.Selection(string="", selection=[('Requested', 'Requested'), ('Authorised', 'Authorised'), ('Approved', 'Approved'), ('Processed', 'Processed'), ('Received', 'Received'), ], required=False, default='Requested', track_visibility='onchange', )


