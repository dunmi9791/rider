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


