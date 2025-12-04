from odoo import models, fields, api, _

class AgedPayableCustomHandlerExtended(models.AbstractModel):
    _inherit = 'account.aged.payable.report.handler'

    def _report_custom_engine_aged_payable_payment_terms(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        if not options.get('calling_line_dict_id'):
            return {'value': [], 'has_sublines': False}
        model, model_id = self.env['account.report']._get_model_info_from_id(options['calling_line_dict_id'])
        if model == 'res.partner' and model_id:
            partner = self.env['res.partner'].browse(model_id)
            payment_term = partner.property_supplier_payment_term_id.name or _('N/A')
            return {
                'value': [(payment_term, {'name': payment_term})],
                'has_sublines': False
            }
        return {'value': [], 'has_sublines': False}


class AgedReceivableCustomHandlerExtended(models.AbstractModel):
    _inherit = 'account.aged.receivable.report.handler'

    def _report_custom_engine_aged_receivable_payment_terms(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        if not options.get('calling_line_dict_id'):
            return {'value': [], 'has_sublines': False}
        model, model_id = self.env['account.report']._get_model_info_from_id(options['calling_line_dict_id'])
        if model == 'res.partner' and model_id:
            partner = self.env['res.partner'].browse(model_id)
            payment_term = partner.property_payment_term_id.name or _('N/A')
            return {
                'value': [(payment_term, {'name': payment_term})],
                'has_sublines': False
            }
        return {'value': [], 'has_sublines': False}
