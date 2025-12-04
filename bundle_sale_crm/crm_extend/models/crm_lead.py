# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class CRMLead(models.Model):
    _inherit = "crm.lead"

    contract_type = fields.Selection([('framework', 'Framework'), ('po', 'PO')], string='Contract')
    contract_attachment_ids = fields.Many2many('ir.attachment', string="PO Attachment")
    margin_percentage = fields.Integer("Margin %")
    margin_amount = fields.Integer("Margin Amt.")

    def write(self, vals):
        stage_won_id = self.env.ref('crm.stage_lead4').id

        for lead in self:
            # Check if stage is being changed to 'Won'
            if 'stage_id' in vals and vals['stage_id'] == stage_won_id:
                # Use updated or current field values
                contract_type = vals.get('contract_type', lead.contract_type)
                margin_percentage = vals.get('margin_percentage', lead.margin_percentage)
                margin_amount = vals.get('margin_amount', lead.margin_amount)
                attachments = vals.get('contract_attachment_ids', lead.contract_attachment_ids)
                date_deadline = vals.get('date_deadline', lead.date_deadline)

                missing_fields = []

                if not contract_type:
                    missing_fields.append("Contract Type")
                if not margin_percentage:
                    missing_fields.append("Margin %")
                if not margin_amount:
                    missing_fields.append("Margin Amt.")

                # Only check attachments if contract_type is 'po'
                if contract_type == 'po' and not attachments:
                    missing_fields.append("Attachments")

                if not date_deadline:
                    missing_fields.append("Expected Closing")

                if missing_fields:
                    raise ValidationError(
                        "You must fill in the following fields before marking the lead as 'Won':\n " +
                        "\n ".join(missing_fields))

        return super(CRMLead, self).write(vals)
