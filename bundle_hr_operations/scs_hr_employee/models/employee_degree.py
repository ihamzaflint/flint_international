from odoo import models, fields


class EmployeeDegree(models.Model):
    _name = "employee.degree"
    _description = "Employee Degree"

    name = fields.Char("Degree")
    code = fields.Char("Code")
