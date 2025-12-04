from odoo import api, fields, models, _


class Employee(models.Model):
    _inherit = 'hr.employee'

    zk_emp_code = fields.Char('ZK Employee Code', index=True)

    _sql_constraints = [
        ('unique_zk_emp_code', 'UNIQUE(zk_emp_code)', 'Employee code already exists')
    ]