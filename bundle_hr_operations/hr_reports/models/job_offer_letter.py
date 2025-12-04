from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class JobOfferLetter(models.Model):
    _name = "job.offer.letter"
    _description = "Job Offer Letter"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "employee_name"
    _order = "id desc"

    employee_name = fields.Char("Employee Name", required=True, store=True)
    resident_id = fields.Char("Resident ID", required=True, store=True)
    joining_date = fields.Date("Joining Date", required=True, store=True)
    job_title = fields.Char("Job Title", required=True, store=True)

    basic_salary = fields.Float("Basic Salary", required=True, store=True)
    job_offer_letter_line_ids = fields.One2many('job.offer.letter.line', 'job_offer_letter_id', string='Job Offer Letter Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft', required=True, store=True)

    # def action_active(self):
    #     for rec in self:
    #         rec.state = 'active'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class JobOfferLetterLine(models.Model):
    _name = "job.offer.letter.line"
    _description = "Job Offer Letter Line"

    job_offer_letter_id = fields.Many2one('job.offer.letter', string='Job Offer')
    allowance_name_en = fields.Char(string='Allowance Name', required=True, store=True)
    allowance_amount = fields.Float(string='Allowance Amount', required=True, store=True)
    allowance_name_ar = fields.Char(string='إسم البدل', required=True, store=True)

