from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from datetime import date


class ReconcileExpense(models.TransientModel):
    _name = 'reconcile.expense'
    _rec_name = 'name'
    _description = 'Reconcile Expense'

    name = fields.Char()
    expense_id = fields.Many2one(comodel_name="expense.rider", string="Expense Ref")
    balance_amount = fields.Float(string="Balance Amount", required=False, related="expense_id.balance")
    mode = fields.Selection(string="Mode of Disburse", selection=[('cash', 'Cash'), ('cheque', 'Cheque'),
                                                                  ('transfer', 'Transfer')], required=False, )
    mode_ref = fields.Char(string="Cheque / Ref", required=False, )
    date = fields.Date(string="Date", required=False, default=date.today())

    def disburse_loan(self):
        disbursement = self.env['disbursements.ranchi']
        vals = {
            'mode_ref': self.mode_ref,
            'loan_id': self.loan_id.id,
            'disbursed_amount': self.disbursed_amount,
            'mode': self.mode,

        }
        disbursement.create(vals)
        self.loan_id.change_state('disbursed')
