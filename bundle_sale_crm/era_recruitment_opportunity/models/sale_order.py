# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    applicant_name = fields.Char(string='Applicant Name')
    applicant_email = fields.Char(string='Email')
    applicant_phone = fields.Char(string='Contact #')
    applicant_nationality = fields.Char(string='Nationality')
    applicant_current_location = fields.Char(string='Current Location')
    applicant_experience = fields.Char(string='Experience')
    applicant_qualification = fields.Char(string='Qualification')
    applicant_current_company = fields.Char(string='Current Company')
    applicant_position = fields.Char(string='Position')
    applicant_notice_period = fields.Char(string='Notice Period')
    applicant_salary_expectation = fields.Float(string="Salary Expectation",
                                                help='Salary Expected in SAR per month (Including Gosi if Saudi)')
    applicant_dependent = fields.Char(string='Dependents (Wife + Kids)')
    applicant_profession = fields.Char(string='Profession on iqama')
    applicant_number_iqama = fields.Char(string='Number of Iqama Transfers')
    applicant_current_salary = fields.Float(string='Current Salary')
    applicant_resume = fields.Binary(string='Resume')
    is_create_from_applicant = fields.Boolean(string='Is Create From Applicant', default=False)
    hr_applicant_id = fields.Many2one('hr.applicant', string='HR Applicant')
    employee_id = fields.Many2one('hr.employee', string="Related Employee", readonly=True)

    def action_view_employee(self):
        """ Opens the created employee record """
        self.ensure_one()
        return {
            'name': 'Employee',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': self.employee_id.id,
            'target': 'current',
        }

    def action_add_service(self):
        self.ensure_one()
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_order_partner_id': self.partner_id.id,
                'default_product_uom': self.env.ref('uom.product_uom_unit').id,
                'default_product_uom_qty': 1,
            },
        }

    def add_line_control(self):
        self.ensure_one()
        return {
            'name': 'Add Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.service.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.is_create_from_applicant:
            employee = self.env['hr.employee'].create({
                'name': self.applicant_name,
                'job_id': self.hr_applicant_id.recruitment_order_id.lead_id.job_id.id if self.hr_applicant_id.recruitment_order_id else self.hr_applicant_id.lead_id.job_id.id,
            })
            self.employee_id = employee.id
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_order_service_line_ids = fields.One2many('sale.order.service.line', 'order_line_id', string='Service Line')
    is_recruitment_service = fields.Boolean(string='Is Recruitment Service',
                                            related='product_id.is_recruitment_service',
                                            store=True, readonly=True)

    def edit_line_control(self):
        return {
            'name': 'Edit Service',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'no_create': True,
                'edit': True,
            },
        }
