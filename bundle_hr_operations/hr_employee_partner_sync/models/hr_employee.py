from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_sync_with_partners(self):
        """Link employees with partners based on matching names."""
        for employee in self.filtered(lambda e: not e.address_id and not e.work_contact_id):
            # Search for partners with matching name
            matching_partner = self.env['res.partner'].search([
                '|',
                ('name', '=ilike', employee.name),
                ('name', '=ilike', employee.name.split()[0] if employee.name else ''),  # Match first name
            ], limit=1)

            if matching_partner:
                try:
                    # Update employee's partner links
                    employee.write({
                        'address_id': matching_partner.id,
                        'work_contact_id': matching_partner.id,
                    })
                except Exception as e:
                    # Log the error and continue with next employee
                    _logger.error(f"Error linking employee {employee.name} to partner: {str(e)}")
                    continue

    @api.model
    def sync_all_employees_with_partners(self):
        """Sync all employees with partners."""
        employees = self.search([])
        employees.action_sync_with_partners()
        return True
