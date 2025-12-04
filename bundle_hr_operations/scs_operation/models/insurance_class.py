from odoo import fields, models, api, _


class InsuranceClass(models.Model):
    _name = "insurance.class"
    _description = "Insurance Class"
    _rec_name = "name"
    _order = "sequence, name"

    name = fields.Char(string="Insurance Class", required=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="Description")
    is_active = fields.Boolean(string="Active", default=True)
    # Cost parameters for different types
    employee_cost = fields.Float(string="Employee Cost", digits='Product Price')
    spouse_cost = fields.Float(string="Spouse Cost", digits='Product Price')
    child_cost = fields.Float(string="Child Cost", digits='Product Price')
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Insurance class code must be unique!'),
    ]

    def name_get(self):
        """Display name with code for better identification"""
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result
