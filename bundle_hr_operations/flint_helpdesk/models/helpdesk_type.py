from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class HelpDeskType(models.Model):
    _inherit = "helpdesk.ticket.type"

    selected_ticket_type_ids = fields.One2many(
        "service.type", "helpdesk_type_id", string="Request Type"
    )
    is_operation = fields.Boolean("Is Operation")
    is_logistics = fields.Boolean("Is Logistics")
    is_hr = fields.Boolean("Is HR")


    @api.constrains("is_operation", "is_logistics", "is_hr")
    def _check_type(self):
        for rec in self:
            if not rec.is_operation and not rec.is_logistics and not rec.is_hr:
                raise ValidationError(_("At least one type should be selected"))
            if rec.is_operation and rec.is_logistics and rec.is_hr:
                raise ValidationError(_("Only one type should be selected"))
            if rec.is_operation and rec.is_logistics:
                raise ValidationError(_("Only one type should be selected"))
            if rec.is_operation and rec.is_hr:
                raise ValidationError(_("Only one type should be selected"))