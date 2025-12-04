# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base_iban.models.res_partner_bank import normalize_iban
import re
import logging

_logger = logging.getLogger(__name__)

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # [sanjay-techvoot] Override create: auto-detect bank from IBAN if bank_id not set.
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically detect bank from IBAN"""
        records = super(ResPartnerBank, self).create(vals_list)
        # Try to detect bank from IBAN for each new record
        for record in records:
            if record.acc_number and not record.bank_id:
                record.set_bank_from_iban()
        return records
    
    # [sanjay-techvoot] Override write: if acc_number updated, auto-set bank_id from IBAN.
    def write(self, vals):
        """Override write to automatically detect bank from IBAN when account number changes"""
        result = super(ResPartnerBank, self).write(vals)
        # If acc_number was updated and bank_id is not set, try to detect bank
        if 'acc_number' in vals and not vals.get('bank_id'):
            for record in self:
                if record.acc_number and not record.bank_id:
                    record.set_bank_from_iban()
        return result

    # [sanjay-techvoot] Extract bank info from IBAN (SA uses pos 4-6, AE uses pos 4-7).
    def get_bank_from_iban(self, iban=None):
        """
        Extract bank information from IBAN number by searching for res.bank.
        """
        if not iban:
            iban = self.acc_number
            
        if not iban:
            return False
            
        # Clean the IBAN (remove spaces and other non-alphanumeric characters)
        clean_iban = normalize_iban(iban)
        if len(clean_iban) < 4:
            return False
            
        country_code = clean_iban[:2].upper()
        bank_code = False
        
        # Extract bank code based on country format
        if country_code == 'SA':  # Saudi Arabia
            if len(clean_iban) >= 6:
                bank_code = clean_iban[4:6]
        elif country_code == 'AE':  # UAE
            if len(clean_iban) >= 7:
                bank_code = clean_iban[4:7]
        # Add more country-specific formats as needed
        
        if not bank_code:
            return False
            
        # Search for bank by BIC/SWIFT code that contains the bank code
        banks = self.env['res.bank'].search([
            '|',
            ('bic', 'ilike', bank_code),
            ('name', 'ilike', bank_code)
        ], limit=1)
        
        return banks and banks[0] or False
    
    # [sanjay-techvoot] Set bank_id automatically from IBAN using get_bank_from_iban.
    def set_bank_from_iban(self):
        """
        Set the bank_id field based on the IBAN number.
        """
        bank = self.get_bank_from_iban()
        if bank:
            self.bank_id = bank.id
            return True
        return False
