""" inherit sale.order """
from odoo import _, api, models, fields
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order',
                 'order_ids.company_id')
    def _compute_sale_data(self):
        """ override odoo function to compute based on new status """
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state not in ('sale', 'done'):
                    quotation_cnt += 1
                if order.state in ('sale', 'done'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id,
                        order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt


    def action_view_sale_quotation(self):
        """ override odoo function to get based on new status """
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('opportunity_id', '=', self.id),
                            ('state', 'not in', ['sale', 'done'])]
        quotations = self.mapped('order_ids').filtered(
            lambda l: l.state not in ('sale', 'done'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    def action_view_sale_order(self):
        """ override odoo function to get based on new status """
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['context'] = {
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id,
        }
        action['domain'] = [('opportunity_id', '=', self.id),
                            ('state', 'in',  ('sale', 'done'))]
        orders = self.mapped('order_ids').filtered(
            lambda l: l.state in ('sale', 'done'))
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

    def _get_approval_validation_model_names(self):
        """ override odoo function to get based on new status """
        res = super(CrmLead, self)._get_approval_validation_model_names()
        res.append('crm.lead')