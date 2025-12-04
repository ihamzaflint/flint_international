from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError


class HrSalaryIncrementLine(models.Model):
    _name = "hr.salary.increment.line"
    _description = "Hr Salary Increment Line"
    _rec_name= "old_value"
    _order = 'sequence'

    @api.depends('old_value', 'new_value')
    def compute_is_changed(self):
        for line in self:
            is_changed = False
            if line.old_value != line.new_value:
                is_changed = True
            line.is_changed = is_changed

    increment_field_id = fields.Many2one('hr.salary.parameter', string='Salary Parameter', ondelete='restrict', readonly=True)
    sequence = fields.Integer(related='increment_field_id.sequence', store=True)
    old_value = fields.Float(string='Old Amount', digits='Payroll', readonly=True)
    new_value = fields.Float(string='New Amount', digits='Payroll')
    increment_id = fields.Many2one('hr.salary.increment', string='Salary Increment', required=True, ondelete='cascade', index=True, copy=False)
    is_changed = fields.Boolean(compute='compute_is_changed', store=True)


class HrSalaryIncrement(models.Model):
    _name = "hr.salary.increment"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Hr Salary Increment"

    @api.depends('increment_lines', 'increment_lines.new_value')
    def _compute_total_new_amount(self):
        for rec in self:
            total_new_amount = 0.0
            if rec.increment_lines:
                for inc_line in rec.increment_lines:
                    total_new_amount += inc_line.new_value
            rec.total_new_amount = total_new_amount

    name = fields.Char(string="Name", required=True, index=True, copy=False, readonly=True)
    effective_date = fields.Date(string="Effective Date", default=fields.Datetime.now, required=True, readonly=True,
                                 tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To approve'), ('approved', 'Approved'), ('cancel', 'Cancel')],
        default='draft', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee ID',
                                  required=True, tracking=True, readonly=False)
    contract_id = fields.Many2one(related='employee_id.contract_id', string='Contract')
    salary_structure_updated = fields.Boolean(string='Structure Updated', readonly=True)
    increment_lines = fields.One2many('hr.salary.increment.line', 'increment_id',
                                      string='Increment Lines', copy=True, readonly=True,
                                      auto_join=True)
    total_new_amount = fields.Float("Total New Amount", compute="_compute_total_new_amount")

    @api.constrains('effective_date')
    def _constrains_effective_date(self):
        for record in self:
            if int(record.effective_date.strftime("%d")) == 31:
                raise UserError(_('Increment can not happen on 31st of month'))


    def get_increment_lines(self):
        parameters = self.env['hr.salary.parameter'].search([], order='sequence')
        for increment in self:
            increment.sudo().increment_lines.unlink()
            lines = []
            contract = increment.contract_id
            for parameter in parameters:
                lines.append((0, 0, {'old_value': getattr(contract, parameter.field_id.name),
                                     'new_value': getattr(contract, parameter.field_id.name),
                                     'increment_field_id':parameter.id,
                                     }))
            increment.increment_lines = lines
        return True

    # cron function, to check if increment is set for a date, update its values in Contract
    def update_increment_in_contract_cron(self):

        increments = self.search([
                # ('effective_date','>=',date.today()),
                ('effective_date','<=',date.today()),
                ('salary_structure_updated','!=',True),
                ('state','=','approved'),
            ])
        for increment in increments:
            contract = increment.contract_id
            for line in increment.increment_lines:
                setattr(contract, line.increment_field_id.field_id.name, line.new_value)
            increment.salary_structure_updated = True

        return True

    # def update_increment_in_contract_cron_past(self):
    #     increments = self.search([
    #             ('salary_structure_updated','!=',True),
    #             ('state','=','approved'),
    #         ])
    #     print("increments: ",increments)
    #     for increment in increments:
    #         contract = increment.contract_id
    #         for line in increment.increment_lines:
    #             setattr(contract, line.increment_field_id.field_id.name, line.new_value)
    #             print("updated")
    #         increment.salary_structure_updated = True
    # 
    #     return True

    def action_submit(self):
        for increment in self:
            if increment.increment_lines.filtered(lambda l: l.is_changed):
                # raise UserError(_('Old value and New value can not be same.'))
                increment.write({'state':'to_approve'})
        return True

    def action_approve(self):
        self.write({'state': 'approved'})
        for increment in self.filtered(lambda l: l.effective_date <= date.today() and l.salary_structure_updated != True):
            contract = increment.contract_id     
            for line in increment.increment_lines:
                setattr(contract, line.increment_field_id.field_id.name, line.new_value)
            payslip = self.env['hr.payslip'].search([('employee_id', '=', contract.employee_id.id), ('state', 'in', ['draft', 'verify']), ('date_to', '>=', date.today()), ('date_from', '<=', date.today())])
            payslip.compute_sheet()
            increment.salary_structure_updated = True
        return True

    def action_cancel(self):
        for record in self:
            if record.salary_structure_updated:
                raise UserError(_('Salary structure updated with these new values, can not cancel now.'))
        self.write({'state': 'cancel'})
        return True

    def action_reset_draft(self):
        self.write({'state': 'draft'})
        return True

    def unlink(self):
        for line in self:
            if line.state not in ['draft', 'cancel']:
                raise UserError(_('You can only delete salary increment in draft state.'))
        return super(HrSalaryIncrement, self).unlink()
