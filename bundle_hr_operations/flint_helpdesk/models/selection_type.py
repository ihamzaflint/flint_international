from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HelpDeskTypeSelection(models.Model):
    _name = "selection.type"
    _description = "Helpdesk Type Selection"

    name = fields.Char(required=True)
    ticket_type_id = fields.Many2one(
        "helpdesk.ticket.type",
        string="Ticket type",
    )

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
    ):
        if self._context.get("type_id"):
            if not args:
                args = []
            args.append(("ticket_type_id", "=", self._context.get("type_id")))

        return super()._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid,
        )


