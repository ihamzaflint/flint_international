import time
from datetime import datetime
from odoo import api, models
from odoo import tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF
from odoo.tools.misc import get_lang


class VacationJobRespnsibiltyDetails(models.AbstractModel):
    _name = 'report.scs_hr_reports.report_vacation_job_template'
    _description = "Vacation Job Responsibility Report"

    def get_data(self, form):
        vals = []
        user_rec_ids = self.env['res.users'].search([])
        for user_rec_id in user_rec_ids:
            res = {}
            res['name'] = user_rec_id.name
            vals.append(res)
        return vals

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        datas = docs.read([])
        report_lines = self.get_data(datas[0])
        return {
                'doc_ids': self.ids,
                'doc_model': model,
                'data': datas,
                'docs': docs,
                'time': time,
                'get_data': report_lines}

