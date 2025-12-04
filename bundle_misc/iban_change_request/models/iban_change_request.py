from odoo import models, fields, api,_
import openpyxl
import base64
from io import BytesIO
from odoo.exceptions import UserError, ValidationError

class IbanChangeRequest(models.Model):
    _name = 'iban.change.request'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "IBAN Change Request"


    name = fields.Char("Name", copy=False, default=lambda self: _("New"), readonly=True)
    employee_id = fields.Many2one('hr.employee',string='Employee')
    acc_number = fields.Char('Account Number')
    bank_id = fields.Many2one('res.bank')
    partner_id = fields.Many2one('res.partner')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('reject', 'Rejected'),
        ('done', 'Done'),
    ], string='Status', default='draft')
    rejection_reason = fields.Text(string='Rejection Reason')

    @api.model
    def create(self, vals_list):
        if vals_list.get('name', _('New')) == _('New'):
            name = self.env['ir.sequence'].next_by_code('iban_request') or _('New')
            vals_list['name'] = name
        return super(IbanChangeRequest, self).create(vals_list)



    def action_reject(self):
        return {
            "name": _("Rejection Reason"),
            "type": "ir.actions.act_window",
            "res_model": "reject.reason.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id, "active_model": self._name},
        }

    def action_submit(self):
        self.state = 'submit'
        hr_manager_group = self.env.ref("hr.group_hr_manager").users
        for user in hr_manager_group:
            self.activity_schedule(
                user_id=user.id,
                note=_("Hello HR Managers Team kindly process this Change IBan request %s") % self.name,
            )

    def action_approve(self):
        self.state = 'approve'

        vals = {
            'acc_number': self.acc_number,
            'bank_id' : self.bank_id.id,
            'partner_id': self.employee_id.address_id.id,
            'acc_holder_name': self.employee_id.address_id.name,
            'is_default_account' : True
        }
        try:
            res_bank = self.env['res.partner.bank'].create(vals)
            if res_bank:
               self.state = 'done'
               self.employee_id.bank_account_id = res_bank.id
               template = self.env.ref('iban_change_request.email_template_change_iban_approve')
               if template:
                   print(template)
                   template.send_mail(self.id, force_send=True, email_values={
                       'email_to': self.employee_id.work_email,
                   })
               # self.activity_schedule(
               #     user_id=self.employee_id.user_id.id,
               #     note=_("Hello %s Please Note That Your IBAN IS Changed") % self.employee_id.name,
               # )
        except Exception as e:
            raise UserError(_("Failed to create Iban Request."))




