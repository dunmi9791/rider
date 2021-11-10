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
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment Journal',
        required=False)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=False)
    mode = fields.Selection(string="Mode of Disburse", selection=[('cash', 'Cash'), ('cheque', 'Cheque'),
                                                                  ('transfer', 'Transfer')], required=False, )
    mode_ref = fields.Char(string="Cheque / Ref", required=False, )
    date = fields.Date(string="Date", required=False, default=date.today())
    reconcile_obj = fields.Many2one('account.move', invisible=1)


    def reconcile_balance(self):
        if self.balance_amount > 0:
            self.reconcile_balance_credit()
        elif self.balance_amount < 0:
            self.reconcile_balance_debit()


    def reconcile_balance_credit(self):
        move ={'ref': self.expense_id.exp_no,
            'journal_id': self.journal_id.id,
            'date': self.date,

            'line_ids': [(0, 0, {
                'account_id': self.expense_id.account_id.id,
                'partner_id': self.expense_id.partner_id.id,
                'name': 'Reconciliation',
                'credit': self.balance_amount,

            }), (0, 0, {
                'account_id': self.journal_id.default_debit_account_id.id,
                'partner_id': self.expense_id.partner_id.id,
                'name': 'Reconciliation',
                'debit': self.balance_amount,
            })]}
        reconcile_obj = self.env['account.move'].create(move)
        reconcile_obj.post()
        self.expense_id.balanced = True
        self.expense_id.fin_reconcile()

    def reconcile_balance_debit(self):
        move = {'ref': self.expense_id.exp_no,
                'journal_id': self.journal_id.id,
                'date': self.date,

                'line_ids': [(0, 0, {
                    'account_id': self.expense_id.account_id.id,
                    'partner_id': self.expense_id.partner_id.id,
                    'name': 'Reconciliation',
                    'debit': abs(self.balance_amount),

                }), (0, 0, {
                    'account_id': self.journal_id.default_debit_account_id.id,
                    'partner_id': self.expense_id.partner_id.id,
                    'name': 'Reconciliation',
                    'credit': abs(self.balance_amount),
                })]}
        reconcile_obj = self.env['account.move'].create(move)
        reconcile_obj.post()
        self.expense_id.balanced = True
        self.expense_id.fin_reconcile()




