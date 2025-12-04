from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.base_iban.models.res_partner_bank import ResPartnerBank
import re

def normalize_iban(iban):
    return re.sub(r'[\W_]', '', iban or '')

def validate_iban(iban):
    iban = normalize_iban(iban)
    if not iban:
        raise ValidationError(_("There is no IBAN code."))

    country_code = iban[:2].lower()
    if country_code not in _map_iban_template:
        raise ValidationError(_("The IBAN is invalid, it should begin with the country code"))

    iban_template = _map_iban_template[country_code]
    if len(iban) != len(iban_template.replace(' ', '')) or not re.fullmatch("[a-zA-Z0-9]+", iban):
        raise ValidationError(_("The IBAN does not seem to be correct. You should have entered something like this %s\n"
            "Where B = National bank code, S = Branch code, C = Account No, k = Check digit", iban_template))

    check_chars = iban[4:] + iban[:4]
    digits = int(''.join(str(int(char, 36)) for char in check_chars))  # BASE 36: 0..9,A..Z -> 0..35
    if digits % 97 != 1:
        raise ValidationError(_("This IBAN does not pass the validation check, please verify it."))


class ResPartnerBankInherit(models.Model):
    _inherit = "res.partner.bank"

    action_type = fields.Selection(string="Bank Account Type",
                                   selection=[('general', 'General'), ('hr', 'HR'), ('treasury', 'Treasury')],
                                   default='general')
    is_default_account = fields.Boolean(string="Default Account")
    is_create_from_employee = fields.Boolean()
    employee_bank_account_id = fields.Many2one('hr.employee', string="Employee Bank Account", ondelete='cascade')

    @api.constrains('acc_number')
    def _check_acc_number_no_spaces(self):
        for record in self:
            if record.acc_number and ' ' in record.acc_number:
                raise ValidationError(
                    _("Spaces are not allowed in the Account Number for this number: %s") % record.acc_number)

    @api.constrains('acc_holder_name')
    def _check_partner_name(self):
        for record in self:
            if record.acc_holder_name and not all(char.isalpha() or char.isspace() for char in record.acc_holder_name):
                raise ValidationError("Symbols or numbers are not allowed in the Account Holder Name.")
            if record.acc_holder_name and len(record.acc_holder_name) > 35:
                raise ValidationError("Account Holder Name cannot exceed 35 characters.")

    @api.model
    def create(self, values):
        res = super(ResPartnerBankInherit, self).create(values)
        if res.action_type == 'hr' and not res.is_create_from_employee:
            if (res.employee_bank_account_id and len(
                    res.employee_bank_account_id.bank_account_ids) == 1 and
                    res.employee_bank_account_id.bank_account_ids.id == res.id):
                res.is_default_account = True

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('acc_number'):
                try:
                    validate_iban(vals['acc_number'])
                    vals['acc_number'] = normalize_iban(vals['acc_number'])
                except ValidationError:
                    pass
        return super(ResPartnerBank, self).create(vals_list)

    def write(self, vals):
        if vals.get('acc_number'):
            try:
                validate_iban(vals['acc_number'])
                vals['acc_number'] = normalize_iban(vals['acc_number'])
            except ValidationError:
                pass
        return super(ResPartnerBank, self).write(vals)

    def unlink(self):
        for record in self.filtered(lambda r: r.action_type == 'hr'):
            if record.employee_bank_account_id:
                bank_accounts = record.employee_bank_account_id.bank_account_ids
                no_default_bank_accounts = len(
                    bank_accounts.filtered(lambda a: a.is_default_account and a.id != record.id))
                no_employee_bank_accounts = len(bank_accounts)
                if no_employee_bank_accounts > 1 > no_default_bank_accounts:
                    raise ValidationError(
                        _("Employee must have at least one default bank account. , Please check employee bank accounts"))
        return super(ResPartnerBankInherit, self).unlink()

    @api.onchange('employee_bank_account_id')
    def _onchange_employee_bank_account_id(self):
        if self.action_type == 'hr':
            if self.employee_bank_account_id and not self.employee_bank_account_id.address_id:
                raise ValidationError(_("You can't create employee bank account for employee not linked with partner"))
            elif self.employee_bank_account_id and self.employee_bank_account_id.address_id:
                self.partner_id = self.employee_bank_account_id.address_id

# Map ISO 3166-1 -> IBAN template, as described here :
# http://en.wikipedia.org/wiki/International_Bank_Account_Number#IBAN_formats_by_country
_map_iban_template = {
    'ad': 'ADkk BBBB SSSS CCCC CCCC CCCC',  # Andorra
    'ae': 'AEkk BBBC CCCC CCCC CCCC CCC',  # United Arab Emirates
    'al': 'ALkk BBBS SSSK CCCC CCCC CCCC CCCC',  # Albania
    'at': 'ATkk BBBB BCCC CCCC CCCC',  # Austria
    'az': 'AZkk BBBB CCCC CCCC CCCC CCCC CCCC',  # Azerbaijan
    'ba': 'BAkk BBBS SSCC CCCC CCKK',  # Bosnia and Herzegovina
    'be': 'BEkk BBBC CCCC CCXX',  # Belgium
    'bg': 'BGkk BBBB SSSS DDCC CCCC CC',  # Bulgaria
    'bh': 'BHkk BBBB CCCC CCCC CCCC CC',  # Bahrain
    'br': 'BRkk BBBB BBBB SSSS SCCC CCCC CCCT N',  # Brazil
    'by': 'BYkk BBBB AAAA CCCC CCCC CCCC CCCC',  # Belarus
    'ch': 'CHkk BBBB BCCC CCCC CCCC C',  # Switzerland
    'cr': 'CRkk BBBC CCCC CCCC CCCC CC',  # Costa Rica
    'cy': 'CYkk BBBS SSSS CCCC CCCC CCCC CCCC',  # Cyprus
    'cz': 'CZkk BBBB SSSS SSCC CCCC CCCC',  # Czech Republic
    'de': 'DEkk BBBB BBBB CCCC CCCC CC',  # Germany
    'dk': 'DKkk BBBB CCCC CCCC CC',  # Denmark
    'do': 'DOkk BBBB CCCC CCCC CCCC CCCC CCCC',  # Dominican Republic
    'ee': 'EEkk BBSS CCCC CCCC CCCK',  # Estonia
    'es': 'ESkk BBBB SSSS KKCC CCCC CCCC',  # Spain
    'fi': 'FIkk BBBB BBCC CCCC CK',  # Finland
    'fo': 'FOkk CCCC CCCC CCCC CC',  # Faroe Islands
    'fr': 'FRkk BBBB BGGG GGCC CCCC CCCC CKK',  # France
    'gb': 'GBkk BBBB SSSS SSCC CCCC CC',  # United Kingdom
    'ge': 'GEkk BBCC CCCC CCCC CCCC CC',  # Georgia
    'gi': 'GIkk BBBB CCCC CCCC CCCC CCC',  # Gibraltar
    'gl': 'GLkk BBBB CCCC CCCC CC',  # Greenland
    'gr': 'GRkk BBBS SSSC CCCC CCCC CCCC CCC',  # Greece
    'gt': 'GTkk BBBB MMTT CCCC CCCC CCCC CCCC',  # Guatemala
    'hr': 'HRkk BBBB BBBC CCCC CCCC C',  # Croatia
    'hu': 'HUkk BBBS SSSC CCCC CCCC CCCC CCCC',  # Hungary
    'ie': 'IEkk BBBB SSSS SSCC CCCC CC',  # Ireland
    'il': 'ILkk BBBS SSCC CCCC CCCC CCC',  # Israel
    'is': 'ISkk BBBB SSCC CCCC XXXX XXXX XX',  # Iceland
    'it': 'ITkk KBBB BBSS SSSC CCCC CCCC CCC',  # Italy
    'jo': 'JOkk BBBB NNNN CCCC CCCC CCCC CCCC CC',  # Jordan
    'kw': 'KWkk BBBB CCCC CCCC CCCC CCCC CCCC CC',  # Kuwait
    'kz': 'KZkk BBBC CCCC CCCC CCCC',  # Kazakhstan
    'lb': 'LBkk BBBB CCCC CCCC CCCC CCCC CCCC',  # Lebanon
    'li': 'LIkk BBBB BCCC CCCC CCCC C',  # Liechtenstein
    'lt': 'LTkk BBBB BCCC CCCC CCCC',  # Lithuania
    'lu': 'LUkk BBBC CCCC CCCC CCCC',  # Luxembourg
    'lv': 'LVkk BBBB CCCC CCCC CCCC C',  # Latvia
    'mc': 'MCkk BBBB BGGG GGCC CCCC CCCC CKK',  # Monaco
    'md': 'MDkk BBCC CCCC CCCC CCCC CCCC',  # Moldova
    'me': 'MEkk BBBC CCCC CCCC CCCC KK',  # Montenegro
    'mk': 'MKkk BBBC CCCC CCCC CKK',  # Macedonia
    'mr': 'MRkk BBBB BSSS SSCC CCCC CCCC CKK',  # Mauritania
    'mt': 'MTkk BBBB SSSS SCCC CCCC CCCC CCCC CCC',  # Malta
    'mu': 'MUkk BBBB BBSS CCCC CCCC CCCC CCCC CC',  # Mauritius
    'nl': 'NLkk BBBB CCCC CCCC CC',  # Netherlands
    'no': 'NOkk BBBB CCCC CCK',  # Norway
    'pk': 'PKkk BBBB CCCC CCCC CCCC CCCC',  # Pakistan
    'pl': 'PLkk BBBS SSSK CCCC CCCC CCCC CCCC',  # Poland
    'ps': 'PSkk BBBB XXXX XXXX XCCC CCCC CCCC C',  # Palestinian
    'pt': 'PTkk BBBB SSSS CCCC CCCC CCCK K',  # Portugal
    'qa': 'QAkk BBBB CCCC CCCC CCCC CCCC CCCC C',  # Qatar
    'ro': 'ROkk BBBB CCCC CCCC CCCC CCCC',  # Romania
    'rs': 'RSkk BBBC CCCC CCCC CCCC KK',  # Serbia
    'sa': 'SAkk BBCC CCCC CCCC CCCC CCCC',  # Saudi Arabia
    'se': 'SEkk BBBB CCCC CCCC CCCC CCCC',  # Sweden
    'si': 'SIkk BBSS SCCC CCCC CKK',  # Slovenia
    'sk': 'SKkk BBBB SSSS SSCC CCCC CCCC',  # Slovakia
    'sm': 'SMkk KBBB BBSS SSSC CCCC CCCC CCC',  # San Marino
    'tn': 'TNkk BBSS SCCC CCCC CCCC CCCC',  # Tunisia
    'tr': 'TRkk BBBB BRCC CCCC CCCC CCCC CC',  # Turkey
    'ua': 'UAkk BBBB BBCC CCCC CCCC CCCC CCCC C',  # Ukraine
    'vg': 'VGkk BBBB CCCC CCCC CCCC CCCC',  # Virgin Islands
    'xk': 'XKkk BBBB CCCC CCCC CCCC',  # Kosovo
}
