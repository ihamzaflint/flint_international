# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models,_
from odoo.exceptions import UserError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def _search_default_journal(self):
        """this is a base method used to retrieve all matching journal with all accounting actions
        also used by account payment so I added new context and got the default  journal anf filtered
        the defaults by my new domain"""
        journal = super(AccountMoveInherit, self)._search_default_journal()
        journal_types = self._get_valid_journal_types()
        if self.env.context.get('not_payment_method'):
            journal = journal.filtered(lambda j: not j.not_payment_method)
            if not journal:
                company_id = self._context.get('default_company_id', self.env.company.id)
                company = self.env['res.company'].browse(company_id)

                error_msg = _(
                    "No journal could be found in company %(company_name)s for any of those types:[ %(journal_types)s ]  And Can Be Used As A Payment Method",
                    company_name=company.display_name,
                    journal_types=', '.join(journal_types),
                )
                raise UserError(error_msg)
        return journal
