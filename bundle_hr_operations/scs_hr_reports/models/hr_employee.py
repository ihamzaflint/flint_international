from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    warning_letter_sequence = fields.Integer("Warning Letter Number")
    extend_probation_sequence = fields.Integer("Probation Period Extend Number")
    bank_loan_req_sequence = fields.Integer("Bank Loan Request Number")
    attestation_certificate_3_seq = fields.Integer("Attestation Certificate 3 Number")
    crops_eng_registartion_seq = fields.Integer("Registration Crops of Engineer Number")
    attestation_certificate_1_seq = fields.Integer("Attestation Certificate 1 Number")
    stc_entry_permit_sequence = fields.Integer("STC Entry Permit Number")
    liter_embassies_sequence = fields.Integer("Liter Embassies Number")
    salary_transfer_form_seq = fields.Integer("Salary Transfer Form Number")
    disclaimer_sequence = fields.Integer("Disclaimer Number")
    sal_intorduction_letter_seq = fields.Integer("Salary Introduction Letter Number")
    passport_id_arabic = fields.Char("Passport No in Arabic")
    visa_no_arabic = fields.Char("ID No in Arabic")
    employment_letter_seq = fields.Integer("Employment Letter Number")