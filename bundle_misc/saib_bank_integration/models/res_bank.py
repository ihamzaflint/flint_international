# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re


class ResBank(models.Model):
    _inherit = 'res.bank'
    
    # [sanjay-techvoot] Constraint to validate BIC format on res.bank.
    # Checks length (>=4) and only uppercase letters.
    @api.constrains('bic')
    def _check_bic_format(self):
        """
        Validate BIC format:
        - Minimum 4 characters
        - All uppercase letters
        """
        for bank in self:
            if bank.bic:
                if len(bank.bic) < 4:
                    raise ValidationError(_("Bank Identifier Code (BIC) must be at least 4 characters long."))
                
                if not re.match(r'^[A-Z]+$', bank.bic):
                    raise ValidationError(_("Bank Identifier Code (BIC) must contain only uppercase letters."))
