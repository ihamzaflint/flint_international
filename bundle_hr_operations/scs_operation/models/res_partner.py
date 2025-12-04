from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_type = fields.Selection([
        ('hotel', 'Hotel'),
        ('insurance', 'Insurance'),
        ('car_rental', 'Car Rental'),
        ('flight', 'Flight'),
        ('courier', 'Courier'),
        ('other', 'Other')],
        string='Vendor Type', copy=False, default='other')

    @api.constrains('name')
    def _check_partner_name(self):
        for record in self:
            # Only apply strict validation to specific vendor types
            if record.vendor_type in ('hotel', 'insurance', 'flight') and record.name:
                # Check for special characters that might cause issues in banking systems
                if any(char in record.name for char in r'!@#$%^*()_+={}[]|\:;"<>,.?/~`'):
                    raise ValidationError("Special characters are not allowed in the Partner Name for %s vendors." % record.vendor_type)
                if record.name and len(record.name) > 35:
                    raise ValidationError("Partner Name cannot exceed 35 characters for %s vendors." % record.vendor_type)