from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AnalyticAccountType(models.Model):
    _name = 'analytic.account.type'
    _description = 'Analytic Account Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    type = fields.Selection([
        ('business_unit', 'Business Unit'),
        ('project', 'Project'),
        ('generic', 'Generic'),
    ], required=True, string="Assigned To", default="generic", tracking=True,
        help="Business Unit: For department/unit analytics\n"
             "Project: For project-based analytics\n"
             "Generic: For general purpose analytics")
    
    name = fields.Char(tracking=True, required=True, 
                      help="Name of the analytic account type")
    prefix = fields.Char(tracking=True, required=True, size=4,
                        help="4-character prefix used for generating analytic account codes")
    auto_create = fields.Boolean(tracking=True,
                               help="If checked, analytic accounts of this type will be automatically created")
    is_root = fields.Boolean("Is Root", default=False, readonly=True,
                           help="Indicates if this is a root level analytic type")
    sequence = fields.Integer("Sequence", default=10, 
                          help="Used to order analytic types in a hierarchical structure")
    active = fields.Boolean(default=True, tracking=True,
                          help="If unchecked, it will allow you to hide the analytic type without removing it")
    
    _sql_constraints = [
        ('prefix_unique', 'unique(prefix)', 
         'Prefix must be unique across all analytic account types!'),
        ('name_unique', 'unique(name)', 
         'Name must be unique across all analytic account types!')
    ]

    @api.constrains('prefix')
    def _check_prefix_format(self):
        for record in self:
            if record.prefix and (len(record.prefix) != 4 or not record.prefix.isalnum()):
                raise ValidationError(_(
                    "Prefix must be exactly 4 alphanumeric characters. Got: %s", record.prefix))

    @api.constrains('type', 'auto_create')
    def _check_type_constraints(self):
        for record in self:
            if record.type == 'project' and not record.auto_create:
                raise ValidationError(_(
                    "Analytic accounts of type 'Project' must be created from the Projects module"))
            if record.type == 'business_unit' and not record.auto_create:
                raise ValidationError(_(
                    "Analytic accounts of type 'Business Unit' must be created from the HR Departments module"))

    def unlink(self):
        for record in self:
            if record.type != 'generic':
                raise ValidationError(_(
                    "You cannot delete analytic types assigned to 'Business Unit' or 'Project'. "
                    "Consider archiving them instead."))
            if record.is_root:
                raise ValidationError(_(
                    "You cannot delete the root analytic type. "
                    "This is a system requirement."))
        return super().unlink()

    def write(self, vals):
        if 'type' in vals:
            new_type = vals['type']
            for record in self:
                if record.auto_create and record.type != new_type:
                    raise ValidationError(_(
                        "You cannot change the type of an auto-created analytic type."))
                if record.is_root:
                    raise ValidationError(_(
                        "You cannot modify the type of the root analytic type."))
        return super().write(vals)

    def toggle_active(self):
        for record in self:
            if record.is_root and not record.active:
                raise ValidationError(_(
                    "You cannot archive the root analytic type."))
        return super().toggle_active()

    @api.model
    def set_sequence_and_root(self):
        """Initialize default analytic account types with proper sequences"""
        types_data = [
            ('analytic_account_type_top_management', {
                'sequence': 1,
                'name': "Top Management",
                'prefix': 'TMng',
                'is_root': True
            }),
            ('analytic_account_type_section', {
                'sequence': 2,
                'name': "Section",
                'prefix': "Sec"
            }),
            ('analytic_account_type_department', {
                'sequence': 3,
                'name': "Department",
                'prefix': "Dept"
            }),
            ('analytic_account_type_project', {
                'sequence': 4,
                'name': "Project",
                'prefix': "Proj"
            })
        ]
        
        for xml_id, values in types_data:
            try:
                self.env.ref(f'analytic_account_parent.{xml_id}').write(values)
            except Exception as e:
                _logger.error(f"Failed to update {xml_id}: {str(e)}")
        
        return True

    def name_get(self):
        """Override to show prefix in display name"""
        result = []
        for record in self:
            name = f"[{record.prefix}] {record.name}" if record.prefix else record.name
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        """Override to ensure proper sequence assignment"""
        if 'sequence' not in vals:
            vals['sequence'] = self.search([], order='sequence desc', limit=1).sequence + 1
        return super().create(vals)