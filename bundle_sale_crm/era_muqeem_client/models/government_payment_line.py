from odoo import api, fields, models


class GovernmentPaymentLine(models.Model):
    _inherit = 'government.payment.line'

    def action_exit_re_entry(self):
        return {
            'name': 'Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'api.access.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def action_final_exit(self):
        return {
            'name': 'Final Exit',
            'type': 'ir.actions.act_window',
            'res_model': 'final.exit.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.final_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }
    def action_extend_exit_entry(self):
        return {
            'name': 'Extend Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'extend.exit.entry.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.extend_exit_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def transfer_iqama_action(self):
        return {
            'name': 'Transfer Iqama',
            'type': 'ir.actions.act_window',
            'res_model': 'transfer.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.transfer_iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def cancel_exit_entry(self):
        return {
            'name': 'Cancel Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'cancell.visa.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.cancell_exit_entry_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def cancel_final_exit_action(self):
        return {
            'name': 'Cancel Final Exit',
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.final.exit.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.cancel_final_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def reprint_exit_entry(self):
        return {
            'name': 'Reprint Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'reprint.visa.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.reprint_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def print_muqeem_report_action(self):
        return {
            'name': 'Print Muqeem Report',
            'type': 'ir.actions.act_window',
            'res_model': 'print.muqeem.report',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.print_muqeem_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def today_request_action(self):
        return {
            'name': 'Today Request',
            'type': 'ir.actions.act_window',
            'res_model': 'today.request.report.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.today_requests_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }
    def renew_iqama_action(self):
        return {
            'name': 'Iqama Renewal',
            'type': 'ir.actions.act_window',
            'res_model': 'renew.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.renew_iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }


class GovernmentPayment(models.Model):
    _inherit = 'government.payment'

    def action_exit_re_entry(self):
        return {
            'name': 'Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'api.access.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def action_final_exit(self):
        return {
            'name': 'Final Exit',
            'type': 'ir.actions.act_window',
            'res_model': 'final.exit.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.final_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }
    def action_extend_exit_entry(self):
        return {
            'name': 'Extend Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'extend.exit.entry.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.extend_exit_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def transfer_iqama_action(self):
        return {
            'name': 'Transfer Iqama',
            'type': 'ir.actions.act_window',
            'res_model': 'transfer.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.transfer_iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def cancel_exit_entry(self):
        return {
            'name': 'Cancel Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'cancell.visa.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.cancell_exit_entry_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def cancel_final_exit_action(self):
        return {
            'name': 'Cancel Final Exit',
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.final.exit.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.cancel_final_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def reprint_exit_entry(self):
        return {
            'name': 'Reprint Exit Re-Entry',
            'type': 'ir.actions.act_window',
            'res_model': 'reprint.visa.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.reprint_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def print_muqeem_report_action(self):
        return {
            'name': 'Print Muqeem Report',
            'type': 'ir.actions.act_window',
            'res_model': 'print.muqeem.report',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.print_muqeem_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }

    def today_request_action(self):
        return {
            'name': 'Today Request',
            'type': 'ir.actions.act_window',
            'res_model': 'today.request.report.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.today_requests_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }
    def renew_iqama_action(self):
        return {
            'name': 'Iqama Renewal',
            'type': 'ir.actions.act_window',
            'res_model': 'renew.iqama.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('era_muqeem_client.renew_iqama_report_form_view').id,
            'target': 'new',
            'context': {'default_employee_id': self.employee_id.id, 'default_iqama_number': self.iqama_no}
        }