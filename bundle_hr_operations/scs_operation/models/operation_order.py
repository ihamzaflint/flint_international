from odoo import fields, models, api


class GovernmentOrderWithoutPayment(models.Model):
    _name = 'operation.order'
    _description = 'Government Order Without Payment'

    name = fields.Char("Name", required=True,default="New", readonly=True)
    date = fields.Date("Date")
    state = fields.Selection([('draft', 'Draft'),
                              ('on_process', 'On Process'),
                              ('on_hold', 'On Hold'),
                              ('done', 'Done')], default='draft', string="State")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    file_no = fields.Char("File No", related="employee_id.registration_number")
    visa_no = fields.Char("Iqama No (National ID) ", related="employee_id.visa_no")
    visa_expire = fields.Date("Iqama Expire", related="employee_id.visa_expire")
    project_id = fields.Many2one('client.project', string="Project",
                                 related="employee_id.project_id")
    service_type_id = fields.Many2one('service.type', string="Service Type")

    def create(self, vals_list):
        res = super(GovernmentOrderWithoutPayment, self).create(vals_list)
        if res.name == 'New':
            res.name = self.env['ir.sequence'].next_by_code('gov_order_without_payment') or 'New'
        return res


    def action_on_process(self):
        self.write({'state': 'on_process'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_hold(self):
        self.write({'state': 'on_hold'})