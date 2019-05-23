# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Orders(models.Model):
    _name = 'order.rider'
    _rec_name = 'name'

    _description = 'orders'

    name = fields.Char()
    partner_id = fields.Many2one(comodel_name="partner.rider", string="Partner", required=False, )
    order_type = fields.Selection(string="Order Type", selection=[('Round', 'Round'), ('Retrieval', 'Retrieval'), ('PCR', 'PCR'), ('DOD', 'DOD'), ], required=False, )
    order_details = fields.Text(string="Order Details", required=False, )


class Partner(models.Model):
    _name = 'partner.rider'
    _rec_name = 'name'
    _description = 'program partners'

    name = fields.Char()


class OrderMemo(models.Model):
    _name = 'ordermemo.rider'
    _rec_name = 'subject'
    _description = 'Order Memo'

    subject = fields.Char(string="Subject")
    employee_from_id = fields.Many2one(comodel_name="res.users", string="From", required=False, )
    employee_to_id = fields.Many2one(comodel_name="res.users", string="To", required=False, )
    employee_copy_ids = fields.Many2many(comodel_name="res.users", relation="", column1="", column2="", string="CC", )
    date = fields.Date(string="Date", required=False, )
    memo_content = fields.HTML(string="",  )



