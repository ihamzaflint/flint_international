from odoo import fields, models, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    partner_id = fields.Many2one('res.partner', string='customer', domain=[('customer_rank', '>', 0)])
    job_id = fields.Many2one('job.list', string='Job name')

