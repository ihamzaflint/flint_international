from odoo import models, fields, api

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    journal_entry_count = fields.Integer(
        string='Journal Entries',
        compute='_compute_journal_entry_count'
    )

    def _compute_journal_entry_count(self):
        for run in self:
            move_ids = run.slip_ids.mapped('move_id')
            run.journal_entry_count = len(move_ids)

    def action_view_journal_entries(self):
        self.ensure_one()
        move_ids = self.slip_ids.mapped('move_id')
        action = {
            'name': 'Journal Entries',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', move_ids.ids)],
            'context': {'create': False}
        }
        return action
