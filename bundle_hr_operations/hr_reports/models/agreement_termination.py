from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AgreementTermination(models.Model):
    _name = "agreement.termination"
    _description = "Agreement Termination"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, store=True)
    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    company_id = fields.Many2one('sister.company', string='Company Name', required=True, store=True)
    id_number = fields.Char(string='ID Number', required=True, store=True)
    iqama_number = fields.Char(string='Iqama Number', required=True, store=True)
    issue_date = fields.Date(string='Issue Date', required=True, store=True, default=fields.Date.context_today)
    agreement_date = fields.Date(string='Agreement Date', required=True, store=True)
    termination_date = fields.Date(string='Termination Date', required=True, store=True,
                                   default=fields.Date.context_today)
    agreement_termination_line_ids = fields.One2many('agreement.termination.line', 'agreement_termination_id',
                                                     string=' Agreement Termination Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], default='draft')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.write({
                'name': rec.employee_id.name or '',
                'name_ar': rec.employee_id.ar_name or '',
                'id_number': rec.employee_id.client_employee_id or '',
                'iqama_number': rec.employee_id.iqama_number or '',
            })

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'


class AgreementTerminationLine(models.Model):
    _name = "agreement.termination.line"
    _description = "Agreement Termination Line"

    agreement_termination_id = fields.Many2one('agreement.termination', string=' Agreement Termination')

    name = fields.Char(string='Name', required=True, store=True)
    name_ar = fields.Char(string='اسم', required=True, store=True)
    signature = fields.Char(string=' Signature', required=True, store=True)
    date = fields.Date(string=' Date', default=fields.Date.context_today, required=True, store=True)
