from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # Add insurance class field to employee model
    insurance_class_id = fields.Many2one(
        'insurance.class', 
        string='Insurance Class',
        tracking=True,
        groups="hr.group_hr_user",
        help="Employee's insurance class used for benefit calculations"
    )
