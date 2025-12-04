
from odoo import _, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_sa_production_csid_json = fields.Char("PCSID JSON", copy=False, groups="base.group_user",
                                               help="Production CSID data received from the Production CSID API "
                                                  "in dumped json format")

    l10n_sa_compliance_csid_json = fields.Char("CCSID JSON", copy=False, groups="base.group_user",
                                               help="Compliance CSID data received from the Compliance CSID API "
                                                    "in dumped json format")