# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def write(self, vals):
        self = self.with_context(skip_we_update=True)
        super(HrContract, self).write(vals)

    def _remove_work_entries(self):
        # overrite to skip work entry updating, its takign more time while uploading the Employee contracts
        if self._context.get('skip_we_update',False):
            return True
        super()._remove_work_entries()

    def _cancel_work_entries(self):
        if self._context.get('skip_we_update',False):
            return True
        super()._cancel_work_entries()

    def _recompute_work_entries(self, date_from, date_to):
        self.ensure_one()
        if self._context.get('skip_we_update',False):
            return True
        super()._recompute_work_entries(date_from, date_to)
