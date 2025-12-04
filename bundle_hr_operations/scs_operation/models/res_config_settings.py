from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gov_pay_default_journal_id = fields.Many2one('account.journal',
                                                 string='Default Journal for Government Payment')
    google_maps_api_key = fields.Char(string='Google Maps API Key',
                                      config_parameter='scs_operation.google_maps_api_key')

    # default_insurance_policy_id = fields.Many2one('insurance.policy',
    #                                              string='Default Insurance Policy')
    auto_create_insurance_bills = fields.Boolean(string='Auto Create Insurance Bills',
                                                default=True,
                                                help='Automatically create insurance bills when order is approved')
    insurance_bill_journal_id = fields.Many2one('account.journal', 
                                               string='Insurance Bills Journal',
                                               domain=[('type', '=', 'purchase')],
                                               help='Journal used for insurance bills')

    @api.model
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        # ICPSudo.set_param('insurance.default_policy_id', self.default_insurance_policy_id.id)
        ICPSudo.set_param('insurance.auto_create_bills', self.auto_create_insurance_bills)
        ICPSudo.set_param('insurance.bill_journal_id', self.insurance_bill_journal_id.id)
        ICPSudo.set_param('scs_operation.gov_pay_default_journal_id',
                                                         self.gov_pay_default_journal_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        account = ICPSudo.get_param('scs_operation.gov_pay_default_journal_id')
        res['gov_pay_default_journal_id'] = int(account) if account else False
        default_policy = ICPSudo.get_param('insurance.default_policy_id')
        # res['default_insurance_policy_id'] = int(default_policy) if default_policy else False
        
        auto_create = ICPSudo.get_param('insurance.auto_create_bills', 'True')
        res['auto_create_insurance_bills'] = auto_create == 'True'
        
        bill_journal = ICPSudo.get_param('insurance.bill_journal_id')
        res['insurance_bill_journal_id'] = int(bill_journal) if bill_journal else False

        return res
