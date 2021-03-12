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

    vehicle_id = fields.Many2one('vehicles.rider', string='Vehicle Chassis No.',
                                 required=True, track_visibility=True, trace_visibility='onchange', readonly=True,
                                 states={'check-in': [('readonly', False)], 'Tech Eval': [('readonly', False)]})
    vehicle_reg_id = fields.Many2one('vehicles.rider', string='Registration Number', readonly=True,
                                     states={'check-in': [('readonly', False)], 'Tech Eval': [('readonly', False)],
                                              'Confirm': [('readonly', False)]},
                                     help="Registration number.")
    vehicle_reg = fields.Char(string='Registration Number', related='vehicle_id.vehicle_registration', readonly=True,

                                          help="Registration number.")
    vehicle_make = fields.Many2one(string='Make', related='vehicle_id.vehicle_make', readonly=True,

                              help="Registration number.")
    vehicle_model = fields.Many2one(string='Model', related='vehicle_id.vehicle_model', readonly=True,

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
    quotation_count = fields.Integer(string="Loans", compute='get_quotation_count', )
    sale_obj = fields.Many2one('sale.order', invisible=1)
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
    ], string='Invoice Status', invisible=1, )
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

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
        sale_obj = self.env['sale.order'].create({'partner_id': self.client.id,
                                                  'partner_invoice_id': self.client.id,
                                                  'partner_shipping_id': self.client.id,
                                                  'jobcard_id': self.id})
        lines = []
        for line in self.operations:
            val = {'product_id': line.parts_id.id,
                   'product_uom_qty': line.quantity,
                   'order_id': sale_obj.id
                                            }
            lines.append(val)

        self.sale_obj = sale_obj
        self.env['sale.order.line'].create(lines)
        self.change_state('Confirm')

    @api.multi
    def parts_released(self):
        self.change_state('parts release')


    @api.multi
    def quality_check(self):
        self.change_state('quality check')

    @api.multi
    def check_out(self):
        if self.sale_obj.state in ['draft', 'sent']:
            self.sale_obj.action_confirm()
        self.invoice_status = self.sale_obj.invoice_status
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

    def get_quotation_count(self):
        count = self.env['sale.order'].search_count([('jobcard_id', '=', self.id)])
        self.quotation_count = count

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
    total_sites = fields.Float(string="Total Sites", compute="_total_sites")
    order_no = fields.Char(string="Order Number", required=False, )
    sample_type = fields.Char(string="Sample Type", )

    @api.one
    @api.depends('order_line.no_sites', )
    def _total_sites(self):
        self.total_sites = sum(site.no_sites for site in self.order_line)

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        company_id = self.company_id.id
        partner_id = self.partner_id
        if partner_id.is_own_journal:
            journal_id = partner_id.journal_id.id
        else:
            journal_id = (self.env['account.invoice'].with_context(company_id=company_id or self.env.user.company_id.id)
                .default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        vinvoice = self.env['account.invoice'].new({'partner_id': self.partner_invoice_id.id})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals.update({
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': company_id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'vehicle_no': self.jobcard_id.vehicle_reg,
            'chassis_no': self.jobcard_id.vehicle_id.chassis_no,
            'odometer': self.jobcard_id.odometer,
            'jobcard': self.jobcard_id.jobcard_no,
            'vehicle_make': self.jobcard_id.vehicle_id.vehicle_make.name,
            'vehicle_model': self.jobcard_id.vehicle_id.vehicle_model.name,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        })
        return invoice_vals


class SampleTransport(models.Model):
    _name = 'sample.transport'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sample Transport Orders'

    name = fields.Char(string="Proforma Number ",
                       default=lambda self: _('New'),
                       requires=False, readonly=True,)
    sample_deliveries = fields.One2many('sample.deliveries', 'order_id', 'Deliveries', required=False)
    template_id = fields.Many2one(comodel_name="sale.order.template", string="Template")
    state = fields.Selection(string="", selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ],
                             required=False, default='draft',  track_visibility=True,
                             trace_visibility='onchange',)
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False, )
    date = fields.Date(string="Date", required=False, )
    start_date = fields.Date(string="Start Date",)
    end_date = fields.Date(string="End Date",)
    sale_obj = fields.Many2one('sale.order', invisible=1)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.onchange('template_id')
    def _onchange_service(self):
        for rec in self:
            lines = [(5, 0, 0)]
            for line in self.template_id.sale_order_template_line_ids:
                val =(0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': 0
                })
                lines.append(val)
            rec.sample_deliveries = lines

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('increment_proforma') or _('New')
        result = super(SampleTransport, self).create(vals)
        return result

    @api.multi
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'confirm'),
                   ]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for sample in self:
            if sample.is_allowed_transition(sample.state, new_state):
                sample.state = new_state
            else:
                msg = _('Moving from %s to %s is not allowed') % (sample.state, new_state)
                raise UserError(msg)

    @api.multi
    def confirm(self):
        sale_obj = self.env['sale.order'].create({'partner_id': self.client_id.id,
                                                  'partner_invoice_id': self.client_id.id,
                                                  'partner_shipping_id': self.client_id.id,
                                                  'delivery_id': self.id})

        lines = []
        for line in self.sample_deliveries:
            val = {'product_id': line.product_id.id,
                   'product_uom_qty': line.quantity,
                   'order_id': sale_obj.id
                   }
            lines.append(val)

        self.sale_obj = sale_obj
        self.env['sale.order.line'].create(lines)

        self.change_state('confirm')


class SampleDeliveries(models.Model):
    _name = 'sample.deliveries'
    _rec_name = 'name'
    _description = 'Sample Deliveries Frequency'

    name = fields.Char()
    order_id = fields.Many2one(comodel_name="sample.transport", string="", required=False, )
    product_id = fields.Many2one(comodel_name="product.product", string="PCR Lab")
    quantity = fields.Float(string="Frequency")


class ClientContract(models.Model):
    _name = 'client.contract'
    _rec_name = 'sub_contract_no'
    _description = 'Contracts'

    name = fields.Char()
    client_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False, )
    sub_contract_no = fields.Char(string="Subcontract Number")
    total_obligated = fields.Float(string="Total Obligated Amount",  required=False, )
    total_spent = fields.Float(string="Total spent through previous invoice", compute="_previous_spent")
    balance = fields.Float(string="Total Remaining", compute="_balance")
    invoice_ids = fields.One2many(comodel_name="account.invoice", inverse_name="contract_id", string="", required=False, )


    @api.one
    @api.depends('invoice_ids')
    def _previous_spent(self):
        self.total_spent = sum(invoice.amount_total for invoice in self.invoice_ids)

    def _balance(self):
        self.balance = self.total_obligated - self.total_spent


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_id = fields.Many2one(comodel_name="client.contract", string="Contract", required=False, )
    total_obligated = fields.Float(string="Total Obligated Amount", required=False,
                                   related="contract_id.total_obligated" )
    total_spent = fields.Float(string="Total spent ", related="contract_id.total_spent", store=True)
    total_less_current = fields.Float(string="Total spent through previous invoice",
                                      compute="_spent_through", store=True)
    balance = fields.Float(string="Total Remaining", related="contract_id.balance", store=True)
    order_no = fields.Char(string="Order Number", required=False, )
    sample_type = fields.Char(string="Sample Type",)
    total_sites = fields.Float(string="Total Sites", compute="_total_sites")
    vehicle_no = fields.Char(string='Vehicle')
    chassis_no = fields.Char(string="Chassis Number")
    odometer = fields.Char(string="Odometer Reading",)
    jobcard = fields.Char(string='Jobcard')
    vehicle_make = fields.Char(string='Vehicle Make')
    vehicle_model = fields.Char(string='Vehicle Model')

    @api.one
    @api.depends('invoice_line_ids.no_sites', )
    def _total_sites(self):
        for sites in self.invoice_line_ids:
            if sites.no_sites:
                self.total_sites = sum(site.no_sites for site in self.order_line)
            else:
                pass

    @api.one
    @api.depends('amount_total')
    def _spent_through(self):
        self.total_less_current = self.total_spent - self.amount_total


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    no_sites = fields.Float(string="Number of Sites",  required=False, )

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        product = self.product_id.with_context(force_company=self.company_id.id)
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
            'no_sites': self.no_sites,
            # 'vehicle_no': self.order_id.jobcard_id.vehichle_reg,
        }
        return res


class InvoiceOrderLine(models.Model):
    _inherit = 'account.invoice.line'

    no_sites = fields.Float(string="Number of Sites", required=False, )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_own_journal = fields.Boolean(string="Enable Own Journal", )
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal",  )


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     @api.multi
#     def _prepare_invoice(self):
#         """
#         Prepare the dict of values to create the new invoice for a sales order. This method may be
#         overridden to implement custom invoice generation (making sure to call super() to establish
#         a clean extension chain).
#         """
#         self.ensure_one()
#         company_id = self.company_id.id
#         partner_id = self.partner_id
#         if partner_id.is_own_journal:
#             journal_id = partner_id.journal_id.id
#         else:
#             journal_id = (self.env['account.invoice'].with_context(company_id=company_id or self.env.user.company_id.id)
#             .default_get(['journal_id'])['journal_id'])
#         if not journal_id:
#             raise UserError(_('Please define an accounting sales journal for this company.'))
#         vinvoice = self.env['account.invoice'].new({'partner_id': self.partner_invoice_id.id})
#         # Get partner extra fields
#         vinvoice._onchange_partner_id()
#         invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
#         invoice_vals.update({
#             'name': self.client_order_ref or '',
#             'origin': self.name,
#             'type': 'out_invoice',
#             'account_id': self.partner_invoice_id.property_account_receivable_id.id,
#             'partner_shipping_id': self.partner_shipping_id.id,
#             'journal_id': journal_id,
#             'currency_id': self.pricelist_id.currency_id.id,
#             'comment': self.note,
#             'payment_term_id': self.payment_term_id.id,
#             'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
#             'company_id': company_id,
#             'user_id': self.user_id and self.user_id.id,
#             'team_id': self.team_id.id,
#             'transaction_ids': [(6, 0, self.transaction_ids.ids)],
#         })
#         return invoice_vals





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
