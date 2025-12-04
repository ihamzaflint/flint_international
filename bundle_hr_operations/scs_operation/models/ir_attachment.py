from odoo import models, fields, api, _


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def run_attachment_script(self):
        employee_families = self.env['hr.employee.family'].sudo().search([])
        for line in employee_families:
            if line.passport_copy:
                attachments = self.env['ir.attachment'].sudo().search([
                    ('id', 'in', line.passport_copy.ids),
                ])
                for att in attachments:
                    att.write({
                            'res_model': 'hr.employee.family',
                            'res_field': 'passport_copy',
                            'res_id': line.id,
                            'public': False,
                        })
                # for att in attachments:
                #     print("Fixing attachment:", att.name)
                #     att.write({
                #         'res_model': 'hr.employee.family',
                #         'res_field': 'passport_copy',
                #         'res_id': line.id,
                #     })
