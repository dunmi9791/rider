# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'name'
    _description = 'Order Memo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Memo Subject", required=False,)

    date = fields.Date(string="", required=False, )
    memo = fields.Html(string="",  )
    order_id = fields.Many2one(comodel_name="order.rider", string="order", required=False, )
    memo_to = fields.Many2one(comodel_name="res.users", string="Memo to", )
    copy_to = fields.Many2many(comodel_name="res.users", string="Copy")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')], 'Status', default='draft',
        copy=False, readonly=True, required=True, track_visibility=True, trace_visibility='onchange', )
    memo_no = fields.Char(string="Memo Number",
                             default=lambda self: _('New'),
                             requires=False, readonly=True, )

    @api.multi
    def order_memo_request(self):
        self.state = 'Requested'

    @api.multi
    def order_memo_approve(self):
        self.state = 'Approved'

    @api.multi
    def order_memo_reject(self):
        self.state = 'Rejected'




    def _track_subtype(self, init_values):
        if 'state' in init_values:
            return 'mail.mt_comment'
        return False

    @api.model
    def create(self, vals):
        if vals.get('memo_no', _('New')) == _('New'):
            vals['memo_no'] = self.env['ir.sequence'].next_by_code('increment_memo') or _('New')
        result = super(OrderMemo, self).create(vals)
        return result
