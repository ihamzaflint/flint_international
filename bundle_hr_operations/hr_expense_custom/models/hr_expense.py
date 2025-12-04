# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    # do not send emails
    def _track_subtype(self, init_values):
        self.ensure_one()
        # if 'state' in init_values and self.state == 'approve':
        #     return self.env.ref('hr_expense.mt_expense_approved')
        # elif 'state' in init_values and self.state == 'cancel':
        #     return self.env.ref('hr_expense.mt_expense_refused')
        # elif 'state' in init_values and self.state == 'done':
        #     return self.env.ref('hr_expense.mt_expense_paid')
        # return super(HrExpenseSheet, self)._track_subtype(init_values)

    def activity_update(self):
        # for expense_report in self.filtered(lambda hol: hol.state == 'submit'):
        #     self.activity_schedule(
        #         'hr_expense.mail_act_expense_approval',
        #         user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        # self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state in ('draft', 'cancel')).activity_unlink(['hr_expense.mail_act_expense_approval'])

    def _send_expense_success_mail(self, msg_dict, expense):
        return True